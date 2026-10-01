from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # PRODUCER, BUYER, ADMIN
    display_name = Column(String(255), nullable=False)
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    producer_profile = relationship(
        "ProducerProfile", back_populates="user", uselist=False
    )
    buyer_profile = relationship("BuyerProfile", back_populates="user", uselist=False)


class ProducerProfile(Base):
    __tablename__ = "producer_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    producer_type = Column(String(50), nullable=False)  # FARMER, FPO
    org_name = Column(String(255), nullable=False)
    state = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    locality = Column(String(255), nullable=True)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    member_farmers = Column(Integer, nullable=True)
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="producer_profile")
    listings = relationship("Listing", back_populates="producer")


class DemandHub(Base):
    __tablename__ = "demand_hubs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    reference_market_name = Column(String(255), nullable=False)

    buyer_profiles = relationship("BuyerProfile", back_populates="hub")


class BuyerProfile(Base):
    __tablename__ = "buyer_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    buyer_type = Column(
        String(50), nullable=False
    )  # RETAILER, RESTAURANT, PROCESSOR, INSTITUTION, CONSUMER_GROUP
    org_name = Column(String(255), nullable=False)
    hub_id = Column(Integer, ForeignKey("demand_hubs.id"), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="buyer_profile")
    hub = relationship("DemandHub", back_populates="buyer_profiles")
    requirements = relationship("Requirement", back_populates="buyer")


class Crop(Base):
    __tablename__ = "crops"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(50), nullable=False)  # VEGETABLE, FRUIT
    agmarknet_commodity_name = Column(String(100), nullable=False)
    shelf_life_days = Column(Integer, nullable=False)
    max_transit_hours = Column(Integer, nullable=False)
    perishability = Column(String(50), nullable=False)  # HIGH, MEDIUM, LOW
    notes = Column(Text, nullable=True)

    listings = relationship("Listing", back_populates="crop")
    requirements = relationship("Requirement", back_populates="crop")


class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    producer_id = Column(Integer, ForeignKey("producer_profiles.id"), nullable=False)
    crop_id = Column(Integer, ForeignKey("crops.id"), nullable=False)
    variety = Column(String(100), nullable=True)
    grade = Column(String(10), nullable=False)  # A, B, C
    quantity_kg = Column(Float, nullable=False)
    quantity_available_kg = Column(Float, nullable=False)
    ask_price_per_kg = Column(Numeric(10, 2), nullable=False)
    min_order_kg = Column(Float, nullable=False)
    harvest_date = Column(Date, nullable=False)
    available_from = Column(Date, nullable=False)
    available_until = Column(Date, nullable=False)
    status = Column(
        String(50), nullable=False, default="ACTIVE"
    )  # ACTIVE, SOLD_OUT, EXPIRED, WITHDRAWN
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        CheckConstraint("quantity_kg > 0", name="chk_listing_qty_pos"),
        CheckConstraint("quantity_available_kg >= 0", name="chk_listing_avail_nonneg"),
        CheckConstraint(
            "quantity_available_kg <= quantity_kg", name="chk_listing_avail_le_total"
        ),
        CheckConstraint("ask_price_per_kg > 0", name="chk_listing_price_pos"),
        CheckConstraint("min_order_kg > 0", name="chk_listing_min_pos"),
        CheckConstraint("min_order_kg <= quantity_kg", name="chk_listing_min_le_total"),
        CheckConstraint(
            "available_until >= available_from", name="chk_listing_date_order"
        ),
        Index("ix_listings_crop_status_until", "crop_id", "status", "available_until"),
    )

    producer = relationship("ProducerProfile", back_populates="listings")
    crop = relationship("Crop", back_populates="listings")


class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    buyer_id = Column(Integer, ForeignKey("buyer_profiles.id"), nullable=False)
    crop_id = Column(Integer, ForeignKey("crops.id"), nullable=False)
    grade_min = Column(String(10), nullable=False)  # A, B, C
    quantity_kg = Column(Float, nullable=False)
    quantity_fulfilled_kg = Column(Float, default=0.0, nullable=False)
    max_landed_price_per_kg = Column(Numeric(10, 2), nullable=False)
    needed_by = Column(Date, nullable=False)
    status = Column(
        String(50), nullable=False, default="OPEN"
    )  # OPEN, PARTIALLY_FULFILLED, FULFILLED, CANCELLED, EXPIRED
    notes = Column(Text, nullable=True)
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("quantity_kg > 0", name="chk_req_qty_pos"),
        CheckConstraint("quantity_fulfilled_kg >= 0", name="chk_req_fulfilled_nonneg"),
        CheckConstraint("max_landed_price_per_kg > 0", name="chk_req_max_price_pos"),
    )

    buyer = relationship("BuyerProfile", back_populates="requirements")
    crop = relationship("Crop", back_populates="requirements")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False)
    requirement_id = Column(Integer, ForeignKey("requirements.id"), nullable=True)
    buyer_id = Column(Integer, ForeignKey("buyer_profiles.id"), nullable=False)
    producer_id = Column(Integer, ForeignKey("producer_profiles.id"), nullable=False)
    crop_id = Column(Integer, ForeignKey("crops.id"), nullable=False)
    quantity_kg = Column(Float, nullable=False)
    agreed_price_per_kg = Column(Numeric(10, 2), nullable=False)
    transport_cost_estimate_per_kg = Column(Numeric(10, 2), nullable=False)
    platform_fee_per_kg = Column(Numeric(10, 2), nullable=False)
    delivery_date = Column(Date, nullable=False)
    status = Column(
        String(50), nullable=False, default="PLACED"
    )  # PLACED, CONFIRMED, REJECTED, CANCELLED, IN_TRANSIT, DELIVERED
    origin = Column(String(50), nullable=False)  # MATCHING, MARKETPLACE
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=True)
    allocated_transport_cost_total = Column(Numeric(10, 2), nullable=True)
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        Index("ix_orders_status", "status"),
        Index("ix_orders_buyer_id", "buyer_id"),
        Index("ix_orders_producer_id", "producer_id"),
    )

    events = relationship("OrderEvent", back_populates="order")


class OrderEvent(Base):
    __tablename__ = "order_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    from_status = Column(String(50), nullable=True)
    to_status = Column(String(50), nullable=False)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    actor_role = Column(String(50), nullable=False)
    note = Column(Text, nullable=True)
    at = Column(DateTime, default=datetime.utcnow, nullable=False)

    order = relationship("Order", back_populates="events")


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    vehicle_type = Column(
        String(50), nullable=False
    )  # MINI_TRUCK, PICKUP, MEDIUM_TRUCK
    capacity_kg = Column(Float, nullable=False)
    cost_per_km = Column(Numeric(10, 2), nullable=False)
    fixed_cost_per_trip = Column(Numeric(10, 2), nullable=False)
    avg_speed_kmph = Column(Float, nullable=False)
    depot_name = Column(String(255), nullable=False)
    depot_lat = Column(Float, nullable=False)
    depot_lng = Column(Float, nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)
    is_demo = Column(Boolean, default=False, nullable=False)


class RoutePlan(Base):
    __tablename__ = "route_plans"

    id = Column(String(36), primary_key=True)  # UUID
    status = Column(
        String(50), nullable=False, default="PROPOSED"
    )  # PROPOSED, APPROVED, DISCARDED
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    approved_at = Column(DateTime, nullable=True)
    method = Column(String(50), nullable=False)  # ORTOOLS, GREEDY_FALLBACK
    solver_status = Column(String(100), nullable=True)
    solve_time_ms = Column(Integer, nullable=False)
    distance_source = Column(
        String(50), nullable=False
    )  # ESTIMATED_HAVERSINE, OSRM_ROAD
    order_ids = Column(JSON, nullable=False)
    num_orders = Column(Integer, nullable=False)
    num_unassigned = Column(Integer, nullable=False)
    baseline_km = Column(Float, nullable=False)
    optimized_km = Column(Float, nullable=False)
    baseline_cost = Column(Numeric(10, 2), nullable=False)
    optimized_cost = Column(Numeric(10, 2), nullable=False)
    result_json = Column(JSON, nullable=False)

    shipments = relationship("Shipment", back_populates="plan")


class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(String(36), ForeignKey("route_plans.id"), nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    status = Column(
        String(50), nullable=False, default="PLANNED"
    )  # PLANNED, DISPATCHED, DELIVERED
    total_distance_km = Column(Float, nullable=False)
    total_cost = Column(Numeric(10, 2), nullable=False)
    total_load_kg = Column(Float, nullable=False)
    peak_load_kg = Column(Float, nullable=False)
    utilization_pct = Column(Float, nullable=False)
    est_duration_min = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    dispatched_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)

    plan = relationship("RoutePlan", back_populates="shipments")
    stops = relationship(
        "ShipmentStop", back_populates="shipment", order_by="ShipmentStop.sequence"
    )


class ShipmentStop(Base):
    __tablename__ = "shipment_stops"

    id = Column(Integer, primary_key=True, autoincrement=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False)
    sequence = Column(Integer, nullable=False)
    stop_type = Column(
        String(50), nullable=False
    )  # DEPOT_START, PICKUP, DROP, DEPOT_END
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    label = Column(String(255), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    load_after_kg = Column(Float, nullable=False)
    cum_distance_km = Column(Float, nullable=False)
    eta_min_from_start = Column(Integer, nullable=False)

    shipment = relationship("Shipment", back_populates="stops")


class MarketPrice(Base):
    __tablename__ = "market_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    hub_id = Column(Integer, ForeignKey("demand_hubs.id"), nullable=False)
    crop_id = Column(Integer, ForeignKey("crops.id"), nullable=False)
    market_name = Column(String(255), nullable=False)
    price_date = Column(Date, nullable=False)
    min_price_per_kg = Column(Numeric(10, 2), nullable=False)
    modal_price_per_kg = Column(Numeric(10, 2), nullable=False)
    max_price_per_kg = Column(Numeric(10, 2), nullable=False)
    source = Column(String(50), nullable=False)  # SYNTHETIC_DEMO, AGMARKNET_SNAPSHOT
    is_synthetic = Column(Boolean, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "hub_id",
            "crop_id",
            "price_date",
            "source",
            name="uq_market_price_hub_crop_date_src",
        ),
    )


class DemandHistory(Base):
    __tablename__ = "demand_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    hub_id = Column(Integer, ForeignKey("demand_hubs.id"), nullable=False)
    crop_id = Column(Integer, ForeignKey("crops.id"), nullable=False)
    date = Column(Date, nullable=False)
    demand_kg = Column(Float, nullable=False)
    avg_price_per_kg = Column(Numeric(10, 2), nullable=False)
    is_synthetic = Column(Boolean, default=True, nullable=False)
    generator_version = Column(String(50), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "hub_id", "crop_id", "date", name="uq_demand_history_hub_crop_date"
        ),
    )
