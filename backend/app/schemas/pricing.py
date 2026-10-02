from pydantic import BaseModel, Field


class WaterfallPerKg(BaseModel):
    farmgate: float = Field(..., description="Producer ask/agreed price per kg (₹)")
    transport: float = Field(..., description="Transport cost per kg (₹)")
    platform_fee: float = Field(..., description="Platform fee per kg (₹)")
    landed: float = Field(..., description="Landed cost per kg = farmgate + transport + platform_fee (₹)")


class WaterfallTotals(BaseModel):
    farmgate_total: float = Field(..., description="Total farmgate payment to producer (₹)")
    transport_total: float = Field(..., description="Total transport cost (₹)")
    platform_fee_total: float = Field(..., description="Total platform fee (₹)")
    landed_total: float = Field(..., description="Total landed order amount (₹)")


class PricingCropInfo(BaseModel):
    id: int
    name: str


class PricingHubInfo(BaseModel):
    id: int
    name: str
    city: str | None = None
    state: str | None = None


class BenchmarkInfo(BaseModel):
    hub: PricingHubInfo
    market_name: str
    price_date: str
    modal_price_per_kg: float
    min_price_per_kg: float
    max_price_per_kg: float
    source: str = Field(..., description="SYNTHETIC_DEMO | AGMARKNET_SNAPSHOT")
    is_synthetic: bool


class ScenarioAssumptions(BaseModel):
    platform_fee_pct: float = Field(2.0, description="Platform fee percentage (cfg)")
    commission_agent_pct: float = Field(5.0, description="Traditional commission agent percentage (cfg)")
    trader_margin_pct: float = Field(8.0, description="Traditional wholesale trader margin percentage (cfg)")
    retail_margin_pct: float = Field(12.0, description="Traditional retail margin percentage (cfg)")
    last_mile_cost_per_kg: float = Field(1.0, description="Traditional local handling & transport per kg (₹)")


class TraditionalScenario(BaseModel):
    farmer_mandi_net_per_kg: float = Field(..., description="Estimated net realization for farmer at APMC Mandi (₹/kg)")
    buyer_traditional_per_kg: float = Field(..., description="Estimated cost for buyer through traditional multi-intermediary chain (₹/kg)")
    delta_farmer_pct: float = Field(..., description="Farmer income change % vs mandi: (farmgate - farmer_mandi_net) / farmer_mandi_net * 100")
    delta_buyer_pct: float = Field(..., description="Buyer cost change % vs traditional: (landed - buyer_traditional) / buyer_traditional * 100")
    assumptions: ScenarioAssumptions


class FairBand(BaseModel):
    low: float = Field(..., description="Lower fair band bound (₹/kg) = farmer_mandi_net")
    high: float = Field(..., description="Upper fair band bound (₹/kg) = (buyer_traditional - transport_per_kg) / (1 + platform_fee_pct/100)")


class TrendPoint(BaseModel):
    date: str
    modal_price_per_kg: float


class OrderPriceBreakdownResponse(BaseModel):
    order_id: int
    crop: PricingCropInfo
    quantity_kg: float
    per_kg: WaterfallPerKg
    totals: WaterfallTotals
    transport_basis: str = Field(..., description="ALLOCATED_ROUTE | ESTIMATE")
    benchmark: BenchmarkInfo | None = None
    scenario: TraditionalScenario | None = None
    fair_band: FairBand | None = None
    basis: str = Field("MODELLED_SCENARIO", description="MODELLED_SCENARIO per API.md §12")
    disclaimer: str = Field(
        "Baseline mandi and traditional-chain metrics are modelled scenarios based on published research parameters and market benchmark prices.",
        description="Integrity disclaimer"
    )


class PricingBenchmarkResponse(BaseModel):
    hub: PricingHubInfo
    benchmark: BenchmarkInfo | None = None
    trend: list[TrendPoint] = Field(default_factory=list, description="30-day modal price trend")
    fair_band: FairBand | None = None
    assumptions: ScenarioAssumptions
    basis: str = Field("MODELLED_SCENARIO", description="MODELLED_SCENARIO per API.md §12")
    disclaimer: str = Field(
        "Reference price is drawn from official Agmarknet snapshots where available, or synthetic market benchmarks for demonstration.",
        description="Integrity disclaimer"
    )
