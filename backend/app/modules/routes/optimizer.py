import time
from typing import Any

from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from app.core.geo import road_distance_km
from app.modules.routes.distance import calculate_distance_matrix


class RouteOptimizer:
    """Capacitated Vehicle Routing Problem with Pickups and Deliveries (PDP) using Google OR-Tools.

    Per ML.md §10.
    """

    def __init__(
        self,
        orders: list[dict[str, Any]],
        vehicles: list[dict[str, Any]],
        time_limit_s: int = 5,
        max_route_minutes: int = 600,
        service_minutes: float = 20.0,
        avg_speed_kmph: float = 30.0,
        circuity: float = 1.35,
    ):
        self.orders = orders
        self.vehicles = vehicles
        self.time_limit_s = time_limit_s
        self.max_route_minutes = max_route_minutes
        self.service_minutes = service_minutes
        self.avg_speed_kmph = avg_speed_kmph
        self.circuity = circuity

    def solve(self) -> dict[str, Any]:
        """Execute OR-Tools optimization, falling back to greedy algorithm if no solution found."""
        start_time = time.time()
        try:
            result = self._solve_ortools()
            elapsed_ms = int((time.time() - start_time) * 1000)
            result["solve_time_ms"] = elapsed_ms
            return result
        except Exception:
            # Fallback to greedy
            result = self._solve_greedy()
            elapsed_ms = int((time.time() - start_time) * 1000)
            result["solve_time_ms"] = elapsed_ms
            result["method"] = "GREEDY_FALLBACK"
            return result

    def _solve_ortools(self) -> dict[str, Any]:
        num_vehicles = len(self.vehicles)
        num_orders = len(self.orders)

        # Build nodes:
        # Depot nodes for each vehicle (start/end)
        # For each vehicle v, start depot node index = v, end depot node index = v + num_vehicles (or reuse start if same)
        # Standard OR-Tools multi-depot modeling:
        # Let starts = [0, 1, ..., num_vehicles - 1]
        # Let ends = [0, 1, ..., num_vehicles - 1] if closed loops returning to same depot
        # Pickup nodes: num_vehicles + 2*i
        # Delivery nodes: num_vehicles + 2*i + 1

        locations: list[tuple[float, float]] = []
        node_types: list[str] = []
        node_labels: list[str] = []
        node_orders: list[int | None] = []

        # Vehicle depots
        starts = []
        ends = []
        for i, v in enumerate(self.vehicles):
            locations.append((v["depot_lat"], v["depot_lng"]))
            node_types.append("DEPOT")
            node_labels.append(f"Depot: {v['depot_name']}")
            node_orders.append(None)
            starts.append(i)
            ends.append(i)

        # Pickup & Delivery nodes
        pickup_indices = []
        delivery_indices = []
        demands = [0] * num_vehicles

        for o in self.orders:
            p_idx = len(locations)
            locations.append((o["pickup_lat"], o["pickup_lng"]))
            node_types.append("PICKUP")
            node_labels.append(f"Pickup #{o['order_id']} ({o['crop_name']}): {o['producer_name']}")
            node_orders.append(o["order_id"])
            demands.append(int(round(o["quantity_kg"])))
            pickup_indices.append(p_idx)

            d_idx = len(locations)
            locations.append((o["delivery_lat"], o["delivery_lng"]))
            node_types.append("DROP")
            node_labels.append(f"Drop #{o['order_id']} ({o['crop_name']}): {o['buyer_name']}")
            node_orders.append(o["order_id"])
            demands.append(-int(round(o["quantity_kg"])))
            delivery_indices.append(d_idx)

        total_nodes = len(locations)
        dist_matrix_km = calculate_distance_matrix(locations, circuity=self.circuity)

        # time in minutes (travel time + service time at destination)
        time_matrix_min = []
        for i in range(total_nodes):
            row = []
            for j in range(total_nodes):
                if i == j:
                    row.append(0)
                else:
                    travel_min = (dist_matrix_km[i][j] / self.avg_speed_kmph) * 60.0
                    service = self.service_minutes if node_types[j] in ["PICKUP", "DROP"] else 0.0
                    row.append(int(round(travel_min + service)))
            time_matrix_min.append(row)

        manager = pywrapcp.RoutingIndexManager(total_nodes, num_vehicles, starts, ends)
        routing = pywrapcp.RoutingModel(manager)

        # Cost callback per vehicle
        # ML.md §10: Arc cost per vehicle = round(cost_per_km * km * 100) (paise)
        def create_cost_callback(v_idx: int):
            cost_per_km = self.vehicles[v_idx]["cost_per_km"]

            def cost_callback(from_index: int, to_index: int) -> int:
                from_node = manager.IndexToNode(from_index)
                to_node = manager.IndexToNode(to_index)
                km = dist_matrix_km[from_node][to_node]
                return int(round(cost_per_km * km * 100))

            return cost_callback

        cost_callback_indices = []
        for v_idx in range(num_vehicles):
            cb = create_cost_callback(v_idx)
            cb_idx = routing.RegisterTransitCallback(cb)
            cost_callback_indices.append(cb_idx)
            routing.SetArcCostEvaluatorOfVehicle(cb_idx, v_idx)
            # Set fixed vehicle cost in paise
            fixed_cost_paise = int(round(self.vehicles[v_idx]["fixed_cost_per_trip"] * 100))
            routing.SetFixedCostOfVehicle(fixed_cost_paise, v_idx)

        # Capacity Dimension
        def demand_callback(from_index: int) -> int:
            from_node = manager.IndexToNode(from_index)
            return demands[from_node]

        demand_callback_idx = routing.RegisterUnaryTransitCallback(demand_callback)
        vehicle_capacities = [int(round(v["capacity_kg"])) for v in self.vehicles]
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_idx,
            0,  # null capacity slack
            vehicle_capacities,
            True,  # start cumul to zero
            "Capacity",
        )
        capacity_dimension = routing.GetDimensionOrDie("Capacity")

        # Time Dimension
        def time_callback(from_index: int, to_index: int) -> int:
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return time_matrix_min[from_node][to_node]

        time_callback_idx = routing.RegisterTransitCallback(time_callback)
        routing.AddDimension(
            time_callback_idx,
            self.max_route_minutes,  # max slack / waiting time
            self.max_route_minutes,  # max route duration
            True,  # start cumul to zero
            "Time",
        )
        time_dimension = routing.GetDimensionOrDie("Time")

        # Pickups and Deliveries constraints
        for i in range(num_orders):
            p_node = pickup_indices[i]
            d_node = delivery_indices[i]
            p_index = manager.NodeToIndex(p_node)
            d_index = manager.NodeToIndex(d_node)

            routing.AddPickupAndDelivery(p_index, d_index)
            routing.solver().Add(routing.VehicleVar(p_index) == routing.VehicleVar(d_index))
            routing.solver().Add(
                time_dimension.CumulVar(p_index) <= time_dimension.CumulVar(d_index)
            )

            # Disjunction with penalty per ML.md §10
            # penalty = max(10 * baseline_chunk_cost_paise, 1_000_000)
            baseline_cost_paise = int(round(self.orders[i].get("baseline_cost", 1000.0) * 100))
            penalty = max(10 * baseline_cost_paise, 1_000_000)
            routing.AddDisjunction([p_index], penalty)
            routing.AddDisjunction([d_index], penalty)

        # Search Parameters
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = self.time_limit_s

        solution = routing.SolveWithParameters(search_parameters)
        if not solution:
            return self._solve_greedy()

        # Extract solution
        shipments: list[dict[str, Any]] = []
        assigned_orders: set[int] = set()

        for v_idx in range(num_vehicles):
            vehicle_info = self.vehicles[v_idx]
            index = routing.Start(v_idx)
            stops = []
            cum_km = 0.0
            seq = 0
            peak_load = 0.0
            prev_node = None

            while not routing.IsEnd(index):
                node = manager.IndexToNode(index)
                load = solution.Value(capacity_dimension.CumulVar(index))
                time_min = solution.Value(time_dimension.CumulVar(index))
                peak_load = max(peak_load, float(load))

                if prev_node is not None:
                    cum_km += dist_matrix_km[prev_node][node]

                st_type = node_types[node]
                if st_type == "DEPOT":
                    st_type = "DEPOT_START"

                stops.append(
                    {
                        "sequence": seq,
                        "stop_type": st_type,
                        "order_id": node_orders[node],
                        "label": node_labels[node],
                        "lat": locations[node][0],
                        "lng": locations[node][1],
                        "load_after_kg": float(load),
                        "cum_distance_km": round(cum_km, 2),
                        "eta_min_from_start": int(time_min),
                    }
                )
                if node_orders[node]:
                    assigned_orders.add(node_orders[node])

                prev_node = node
                seq += 1
                index = solution.Value(routing.NextVar(index))

            # End depot
            end_node = manager.IndexToNode(index)
            if prev_node is not None:
                cum_km += dist_matrix_km[prev_node][end_node]
            end_time_min = solution.Value(time_dimension.CumulVar(index))

            stops.append(
                {
                    "sequence": seq,
                    "stop_type": "DEPOT_END",
                    "order_id": None,
                    "label": f"Depot Return: {vehicle_info['depot_name']}",
                    "lat": locations[end_node][0],
                    "lng": locations[end_node][1],
                    "load_after_kg": 0.0,
                    "cum_distance_km": round(cum_km, 2),
                    "eta_min_from_start": int(end_time_min),
                }
            )

            # If vehicle only visited depots, skip
            if len(stops) > 2:
                # Calculate cost: fixed + cost_per_km * round_trip_km
                trip_cost = vehicle_info["fixed_cost_per_trip"] + (
                    vehicle_info["cost_per_km"] * cum_km
                )
                utilization = round((peak_load / vehicle_info["capacity_kg"]) * 100, 1)

                shipments.append(
                    {
                        "temp_id": f"s{len(shipments)+1}",
                        "shipment_id": None,
                        "vehicle": {
                            "id": vehicle_info["id"],
                            "name": vehicle_info["name"],
                            "vehicle_type": vehicle_info["vehicle_type"],
                            "capacity_kg": float(vehicle_info["capacity_kg"]),
                        },
                        "total_distance_km": round(cum_km, 2),
                        "total_cost": round(trip_cost, 2),
                        "peak_load_kg": round(peak_load, 1),
                        "utilization_pct": utilization,
                        "est_duration_min": int(end_time_min),
                        "stops": stops,
                        "geometry": [[s["lat"], s["lng"]] for s in stops],
                    }
                )

        # Unassigned orders
        unassigned: list[dict[str, Any]] = []
        for o in self.orders:
            if o["order_id"] not in assigned_orders:
                reason = "CAPACITY"
                max_veh_cap = max(v["capacity_kg"] for v in self.vehicles)
                if o["quantity_kg"] > max_veh_cap:
                    reason = "CAPACITY"
                else:
                    reason = "NO_FEASIBLE_INSERTION"
                unassigned.append(
                    {
                        "order_id": o["order_id"],
                        "quantity_kg": float(o["quantity_kg"]),
                        "reason": reason,
                    }
                )

        return {
            "method": "ORTOOLS",
            "solver_status": "OPTIMAL" if solution else "FEASIBLE",
            "shipments": shipments,
            "unassigned": unassigned,
        }

    def _solve_greedy(self) -> dict[str, Any]:
        """Greedy fallback insertion per ML.md §10:

        Sort orders by descending direct distance, insert into best vehicle.
        """
        # Sort orders by direct distance descending
        sorted_orders = sorted(
            self.orders,
            key=lambda o: road_distance_km(
                (o["pickup_lat"], o["pickup_lng"]),
                (o["delivery_lat"], o["delivery_lng"]),
                circuity=self.circuity,
            ),
            reverse=True,
        )

        shipments: list[dict[str, Any]] = []
        unassigned: list[dict[str, Any]] = []

        available_vehicles = [dict(v) for v in self.vehicles]

        for o in sorted_orders:
            qty = float(o["quantity_kg"])
            # Find smallest unused vehicle with capacity >= qty
            fitting_idx = None
            best_cap = float("inf")
            for idx, v in enumerate(available_vehicles):
                if v["capacity_kg"] >= qty and v["capacity_kg"] < best_cap:
                    best_cap = v["capacity_kg"]
                    fitting_idx = idx

            if fitting_idx is None:
                unassigned.append(
                    {
                        "order_id": o["order_id"],
                        "quantity_kg": qty,
                        "reason": "CAPACITY" if qty > max(v["capacity_kg"] for v in self.vehicles) else "NO_FEASIBLE_INSERTION",
                    }
                )
                continue

            # Assign to this vehicle
            v = available_vehicles.pop(fitting_idx)
            depot_coords = (v["depot_lat"], v["depot_lng"])
            p_coords = (o["pickup_lat"], o["pickup_lng"])
            d_coords = (o["delivery_lat"], o["delivery_lng"])

            d1 = road_distance_km(depot_coords, p_coords, self.circuity)
            d2 = road_distance_km(p_coords, d_coords, self.circuity)
            d3 = road_distance_km(d_coords, depot_coords, self.circuity)
            total_km = round(d1 + d2 + d3, 2)

            t1 = int(round((d1 / self.avg_speed_kmph) * 60 + self.service_minutes))
            t2 = int(round(t1 + (d2 / self.avg_speed_kmph) * 60 + self.service_minutes))
            t3 = int(round(t2 + (d3 / self.avg_speed_kmph) * 60))

            if t3 > self.max_route_minutes:
                # Duration exceeded
                unassigned.append(
                    {
                        "order_id": o["order_id"],
                        "quantity_kg": qty,
                        "reason": "DURATION",
                    }
                )
                available_vehicles.append(v)
                continue

            trip_cost = round(v["fixed_cost_per_trip"] + (v["cost_per_km"] * total_km), 2)
            utilization = round((qty / v["capacity_kg"]) * 100, 1)

            stops = [
                {
                    "sequence": 0,
                    "stop_type": "DEPOT_START",
                    "order_id": None,
                    "label": f"Depot: {v['depot_name']}",
                    "lat": depot_coords[0],
                    "lng": depot_coords[1],
                    "load_after_kg": 0.0,
                    "cum_distance_km": 0.0,
                    "eta_min_from_start": 0,
                },
                {
                    "sequence": 1,
                    "stop_type": "PICKUP",
                    "order_id": o["order_id"],
                    "label": f"Pickup #{o['order_id']} ({o['crop_name']}): {o['producer_name']}",
                    "lat": p_coords[0],
                    "lng": p_coords[1],
                    "load_after_kg": qty,
                    "cum_distance_km": d1,
                    "eta_min_from_start": t1,
                },
                {
                    "sequence": 2,
                    "stop_type": "DROP",
                    "order_id": o["order_id"],
                    "label": f"Drop #{o['order_id']} ({o['crop_name']}): {o['buyer_name']}",
                    "lat": d_coords[0],
                    "lng": d_coords[1],
                    "load_after_kg": 0.0,
                    "cum_distance_km": round(d1 + d2, 2),
                    "eta_min_from_start": t2,
                },
                {
                    "sequence": 3,
                    "stop_type": "DEPOT_END",
                    "order_id": None,
                    "label": f"Depot Return: {v['depot_name']}",
                    "lat": depot_coords[0],
                    "lng": depot_coords[1],
                    "load_after_kg": 0.0,
                    "cum_distance_km": total_km,
                    "eta_min_from_start": t3,
                },
            ]

            shipments.append(
                {
                    "temp_id": f"s{len(shipments)+1}",
                    "shipment_id": None,
                    "vehicle": {
                        "id": v["id"],
                        "name": v["name"],
                        "vehicle_type": v["vehicle_type"],
                        "capacity_kg": float(v["capacity_kg"]),
                    },
                    "total_distance_km": total_km,
                    "total_cost": trip_cost,
                    "peak_load_kg": qty,
                    "utilization_pct": utilization,
                    "est_duration_min": t3,
                    "stops": stops,
                    "geometry": [[s["lat"], s["lng"]] for s in stops],
                }
            )

        return {
            "method": "GREEDY_FALLBACK",
            "solver_status": "FEASIBLE",
            "shipments": shipments,
            "unassigned": unassigned,
        }
