"""
mcp_servers/travel_inventory_mcp_server.py
Travel Inventory MCP Server — flight, hotel, car, and insurance tools.
Runs on port 8002.
"""

from fastmcp import FastMCP
from services.flight_service import (
    search_flights, search_flexible_dates, get_flight_details,
    get_flight_booking, book_flight, cancel_flight,
    check_cancellation_terms, reschedule_flight, upgrade_cabin,
    get_bookings_by_customer as get_flight_bookings_by_customer,
)
from services.hotel_service import (
    search_hotels, get_hotel_details, get_hotel_booking,
    book_hotel, cancel_hotel, modify_hotel_booking,
    get_bookings_by_customer as get_hotel_bookings_by_customer,
)
from services.car_service import (
    search_cars, get_car_details, get_car_booking,
    book_car, cancel_car, extend_rental, change_pickup_location,
    get_bookings_by_customer as get_car_bookings_by_customer,
)
from services.insurance_service import (
    get_insurance_policy, get_policy_by_booking, get_policies_by_customer,
    check_coverage, check_cancellation_coverage, file_claim,
    get_claim_status, cancel_insurance, update_insurance_travel_dates,
    compare_plans,
)

mcp = FastMCP(
    name="travel-inventory-mcp-server",
    instructions="Tools for flights, hotels, cars, and insurance. Cancellation refunds are calculated by policy tiers. Refunds above $500 require supervisor approval.",
)


# ─── FLIGHT TOOLS ─────────────────────────────────────────────────────────────

@mcp.tool()
def search_flights_tool(
    origin: str,
    destination: str,
    travel_date: str,
    cabin_class: str = None,
    passengers: int = 1,
    preferred_airline: str = None,
    max_price: float = None,
) -> dict:
    """
    Searches available flights by IATA route codes, date (YYYY-MM-DD), and filters.
    Returns flights sorted by price ascending with availability and amenities.
    Use origin/destination as IATA codes (e.g. JFK, LHR, DXB).
    """
    return search_flights(origin, destination, travel_date, cabin_class, passengers, preferred_airline, max_price)


@mcp.tool()
def search_flexible_dates_tool(
    origin: str,
    destination: str,
    dates: list,
    cabin_class: str = None,
    passengers: int = 1,
) -> dict:
    """
    Searches across multiple dates and returns cheapest available flight per date.
    Use when customer is flexible on travel dates and wants the best price.
    dates: list of YYYY-MM-DD strings.
    """
    return search_flexible_dates(origin, destination, dates, cabin_class, passengers)


@mcp.tool()
def get_flight_details_tool(flight_id: str) -> dict:
    """
    Returns complete flight details: route, times, price, aircraft, amenities,
    and the full cancellation policy with refund tiers.
    Call before booking to confirm details with the customer.
    """
    return get_flight_details(flight_id)


@mcp.tool()
def get_flight_booking_tool(booking_id: str) -> dict:
    """
    Returns full flight booking details including flight info, fare breakdown,
    and current cancellation eligibility (refund amount if cancelled now).
    Use when customer asks about an existing flight booking.
    """
    return get_flight_booking(booking_id)


@mcp.tool()
def book_flight_tool(
    flight_id: str,
    customer_id: str,
    cabin_class: str,
    passengers: int = 1,
    meal_preferences: str = None,
    special_requests: str = None,
) -> dict:
    """
    Creates a confirmed flight booking and deducts seat availability.
    Earns 1 loyalty point per $1 spent.
    Returns booking reference and confirmation details.
    Call verify_passport_tool first for international flights.
    """
    return book_flight(flight_id, customer_id, cabin_class, passengers, meal_preferences, special_requests)


@mcp.tool()
def cancel_flight_tool(booking_id: str, reason: str) -> dict:
    """
    Cancels a confirmed flight booking and calculates refund by policy:
    > 72 hours before departure = 100% refund
    24-72 hours before = 50% refund
    < 24 hours before = 0% refund
    HARD RULE: Refund above $500 sets requires_supervisor_approval=true.
    When this happens, stop and inform customer that approval is needed.
    Do not attempt to process the refund directly.
    """
    return cancel_flight(booking_id, reason)


@mcp.tool()
def check_flight_cancellation_terms_tool(booking_id: str) -> dict:
    """
    Returns what refund the customer would receive RIGHT NOW if they cancel.
    Read-only — does not cancel the booking.
    Use when customer asks about cancellation terms before deciding.
    """
    return check_cancellation_terms(booking_id)


@mcp.tool()
def reschedule_flight_tool(booking_id: str, new_flight_id: str) -> dict:
    """
    Reschedules a flight to a different flight on the same route.
    If the new flight costs more, the fare difference is charged.
    If cheaper, no refund is issued (standard reschedule policy).
    """
    return reschedule_flight(booking_id, new_flight_id)


@mcp.tool()
def upgrade_flight_cabin_tool(booking_id: str, target_cabin: str) -> dict:
    """
    Upgrades a booking to a higher cabin class (economy → business → first).
    Charges the fare difference as an upgrade cost.
    target_cabin: 'business' or 'first'.
    """
    return upgrade_cabin(booking_id, target_cabin)


@mcp.tool()
def get_flight_bookings_by_customer_tool(customer_id: str) -> dict:
    """
    Returns all flight bookings for a customer separated into active and cancelled.
    Use to get an overview of a customer's flight history.
    """
    return get_flight_bookings_by_customer(customer_id)


# ─── HOTEL TOOLS ──────────────────────────────────────────────────────────────

@mcp.tool()
def search_hotels_tool(
    city: str,
    check_in: str,
    check_out: str,
    adults: int = 1,
    children: int = 0,
    category: str = None,
    min_star_rating: int = None,
    max_price_per_night: float = None,
    required_amenities: list = None,
    meal_plan: str = None,
) -> dict:
    """
    Searches available hotels by city and date range with full filtering.
    category: 'luxury', 'business', 'leisure', 'budget'.
    meal_plan: 'room_only', 'breakfast', 'half_board', 'full_board'.
    Returns hotels sorted by star rating desc, then price asc.
    check_in and check_out format: YYYY-MM-DD.
    """
    return search_hotels(city, check_in, check_out, adults, children, category, min_star_rating, max_price_per_night, required_amenities, meal_plan)


@mcp.tool()
def get_hotel_details_tool(hotel_id: str) -> dict:
    """
    Returns complete hotel details: description, all room types with prices,
    available meal plans, amenities, and cancellation policy tiers.
    Call before booking to confirm room type availability with customer.
    """
    return get_hotel_details(hotel_id)


@mcp.tool()
def get_hotel_booking_tool(booking_id: str) -> dict:
    """
    Returns full hotel booking details: hotel info, room type, meal plan,
    dates, fare breakdown, and current cancellation terms.
    Use when customer asks about an existing hotel booking.
    """
    return get_hotel_booking(booking_id)


@mcp.tool()
def book_hotel_tool(
    hotel_id: str,
    customer_id: str,
    room_type: str,
    check_in: str,
    check_out: str,
    adults: int = 1,
    children: int = 0,
    meal_plan: str = None,
    special_requests: str = None,
) -> dict:
    """
    Creates a confirmed hotel booking and deducts room availability.
    Earns 1 loyalty point per $1 spent.
    room_type must match one of the hotel's available room types.
    check_in and check_out format: YYYY-MM-DD.
    """
    return book_hotel(hotel_id, customer_id, room_type, check_in, check_out, adults, children, meal_plan, special_requests)


@mcp.tool()
def cancel_hotel_tool(booking_id: str, reason: str) -> dict:
    """
    Cancels a hotel booking and calculates refund by policy:
    > 7 days before check-in = 100% refund
    3-7 days before = 50% refund
    < 3 days before = 0% refund
    HARD RULE: Refund above $500 sets requires_supervisor_approval=true.
    Stop and inform customer that supervisor approval is required.
    """
    return cancel_hotel(booking_id, reason)


@mcp.tool()
def modify_hotel_booking_tool(
    booking_id: str,
    new_check_in: str = None,
    new_check_out: str = None,
    new_room_type: str = None,
    new_meal_plan: str = None,
    add_special_request: str = None,
) -> dict:
    """
    Modifies an existing hotel booking: dates, room type, meal plan, or special requests.
    Price is recalculated if dates or room type change.
    Any price increase is charged to the customer's default payment method.
    Provide only the fields you want to change.
    """
    return modify_hotel_booking(booking_id, new_check_in, new_check_out, new_room_type, new_meal_plan, add_special_request)


@mcp.tool()
def get_hotel_bookings_by_customer_tool(customer_id: str) -> dict:
    """
    Returns all hotel bookings for a customer with status, dates, and hotel info.
    Use to get an overview of a customer's hotel history.
    """
    return get_hotel_bookings_by_customer(customer_id)


# ─── CAR TOOLS ────────────────────────────────────────────────────────────────

@mcp.tool()
def search_cars_tool(
    city: str,
    pickup_date: str,
    return_date: str,
    category: str = None,
    passengers: int = None,
    transmission: str = None,
    max_price_per_day: float = None,
    vendor_type: str = None,
) -> dict:
    """
    Searches available cars by city and date range with filtering.
    category: 'economy', 'suv', 'luxury'.
    transmission: 'automatic' or 'manual'.
    vendor_type: 'corporate', 'local', 'premium'.
    Returns total price for the full rental period.
    """
    return search_cars(city, pickup_date, return_date, category, passengers, transmission, max_price_per_day, vendor_type)


@mcp.tool()
def get_car_details_tool(car_id: str) -> dict:
    """
    Returns complete car details: make, model, features, mileage limit,
    transmission, and full cancellation policy tiers.
    mileage_limit_per_day: null means unlimited mileage.
    """
    return get_car_details(car_id)


@mcp.tool()
def get_car_booking_tool(booking_id: str) -> dict:
    """
    Returns full car rental booking: pickup/return locations and times,
    rental duration, total price, and car details.
    Use when customer asks about an existing car rental.
    """
    return get_car_booking(booking_id)


@mcp.tool()
def book_car_tool(
    car_id: str,
    customer_id: str,
    pickup_location: str,
    pickup_date: str,
    pickup_time: str,
    return_location: str,
    return_date: str,
    return_time: str,
    additional_drivers: int = 0,
    child_seats: int = 0,
) -> dict:
    """
    Creates a confirmed car rental and marks the car as unavailable.
    Earns 1 loyalty point per $1 spent.
    pickup_date and return_date format: YYYY-MM-DD.
    pickup_time and return_time format: HH:MM (24-hour).
    """
    return book_car(car_id, customer_id, pickup_location, pickup_date, pickup_time, return_location, return_date, return_time, additional_drivers, child_seats)


@mcp.tool()
def cancel_car_tool(booking_id: str, reason: str) -> dict:
    """
    Cancels a car rental and calculates refund by policy:
    > 48 hours before pickup = 100% refund
    12-48 hours before = 50% refund
    < 12 hours before = 0% refund
    HARD RULE: Refund above $500 sets requires_supervisor_approval=true.
    Stop and inform customer that supervisor approval is required.
    """
    return cancel_car(booking_id, reason)


@mcp.tool()
def extend_rental_tool(booking_id: str, new_return_date: str, new_return_time: str) -> dict:
    """
    Extends a car rental to a later return date.
    Charges extra days at the same daily rate.
    new_return_date must be after the current return date.
    """
    return extend_rental(booking_id, new_return_date, new_return_time)


@mcp.tool()
def change_pickup_location_tool(booking_id: str, new_pickup_location: str) -> dict:
    """
    Changes the pickup location for a confirmed car rental.
    Use when customer needs to pick up from a different location.
    """
    return change_pickup_location(booking_id, new_pickup_location)


@mcp.tool()
def get_car_bookings_by_customer_tool(customer_id: str) -> dict:
    """
    Returns all car rental bookings for a customer with status and details.
    Use to get an overview of a customer's rental history.
    """
    return get_car_bookings_by_customer(customer_id)


# ─── INSURANCE TOOLS ──────────────────────────────────────────────────────────

@mcp.tool()
def get_insurance_policy_tool(policy_id: str) -> dict:
    """
    Returns full insurance policy details: coverage amounts, premium,
    active dates, and complete claims history.
    Use when customer asks about their policy or coverage details.
    """
    return get_insurance_policy(policy_id)


@mcp.tool()
def get_policy_by_booking_tool(booking_id: str) -> dict:
    """
    Finds the insurance policy linked to a specific booking.
    Returns has_insurance=false if no policy exists for this booking.
    Use before filing a claim to confirm the booking has coverage.
    """
    return get_policy_by_booking(booking_id)


@mcp.tool()
def get_policies_by_customer_tool(customer_id: str) -> dict:
    """
    Returns all insurance policies for a customer across all their bookings.
    Use when customer asks about all their active insurance coverage.
    """
    return get_policies_by_customer(customer_id)


@mcp.tool()
def check_coverage_tool(policy_id: str, claim_type: str) -> dict:
    """
    Checks if a specific claim type is covered under the policy.
    Returns is_covered flag, coverage limit, and covered conditions.
    claim_type examples: 'trip_cancellation', 'medical', 'baggage_loss', 'travel_delay'.
    Use before filing a claim to confirm eligibility.
    """
    return check_coverage(policy_id, claim_type)


@mcp.tool()
def check_cancellation_coverage_tool(policy_id: str, cancellation_reason: str) -> dict:
    """
    Checks if a specific cancellation reason qualifies for trip cancellation benefit.
    Covered reasons include: illness, death, severe weather, job loss, jury duty.
    NOT covered: change of mind, financial reasons, pre-existing conditions (unless waiver).
    """
    return check_cancellation_coverage(policy_id, cancellation_reason)


@mcp.tool()
def file_claim_tool(
    policy_id: str,
    claim_type: str,
    amount_requested: float,
    description: str,
    incident_date: str,
) -> dict:
    """
    Files a new insurance claim against an active policy.
    HARD RULE: Claim amount is automatically capped at the policy maximum.
    Policy must be active. incident_date format: YYYY-MM-DD.
    Call check_coverage_tool first to confirm eligibility before filing.
    """
    return file_claim(policy_id, claim_type, amount_requested, description, incident_date)


@mcp.tool()
def get_claim_status_tool(policy_id: str, claim_id: str) -> dict:
    """
    Returns current status of a filed claim: filed, under_review, approved, rejected, or paid.
    Use when customer asks about the progress of their insurance claim.
    """
    return get_claim_status(policy_id, claim_id)


@mcp.tool()
def cancel_insurance_tool(policy_id: str, reason: str) -> dict:
    """
    Cancels an insurance policy and processes a 50% premium refund.
    HARD RULE: Cannot cancel if there are pending or under-review claims.
    Resolve all active claims before attempting cancellation.
    """
    return cancel_insurance(policy_id, reason)


@mcp.tool()
def update_insurance_dates_tool(
    policy_id: str,
    new_start_date: str,
    new_end_date: str,
) -> dict:
    """
    Updates the travel dates on an insurance policy after a flight reschedule.
    Call this whenever a flight or hotel is rescheduled to keep coverage aligned.
    Date format: YYYY-MM-DD.
    """
    return update_insurance_travel_dates(policy_id, new_start_date, new_end_date)


@mcp.tool()
def compare_insurance_plans_tool() -> dict:
    """
    Returns all available insurance plans with premiums and coverage amounts.
    Use when customer wants to compare options before purchasing.
    Premium is calculated as a percentage of total trip cost.
    """
    return compare_plans()


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8002)