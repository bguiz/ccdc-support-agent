import json
import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from mock_data import CUSTOMERS, ORDERS

load_dotenv()

# init MCP server with a name (snake case)
mcp = FastMCP("support-agent-tools")

@mcp.tool()
def get_customer(query: str, session_state: dict) -> str:
    """
    Fetch a customer by matching against multiple possible identifiers:
    name, email address, or customer ID.
    Returns: Full customer profile, which includes:
    account status, contact details, list of order IDs.
    When to use: Verify who your are speaking with OR retrieve account info.
    When not to use: Look up order details -> lookup_order instead.

    Args:
        query: Search term that is one of name, email address, or customer ID
               e.g. "sarah chen", "sarah@foo.bar", or "CUST-1234"
    """

    # Normalize input for consistent matching (ignore case + extra spaces)
    query = query.strip().lower()

    # Iterate through all customers in the dataset
    for customer in CUSTOMERS.values():
        # Match against customer_id, email, or name
        # This makes the tool flexible in how it can be called
        if (
            query == customer["customer_id"].lower()
            or query == customer["email"].lower()
            or query == customer["name"].lower()
        ):
            # update session state
            session_state["verified_customer_id"] = customer["customer_id"]
            session_state["verified_customer_name"] = customer["name"]

            # Return the matched customer as a JSON string
            return json.dumps(customer)

    if ((not query.startswith('CUST-')) and (query.find('@') == -1)):
      return json.dumps({
        "error": {
          "type": "validation",
          "retryable": False,
          "message": (
              f"Customer ID '{query}' is invalid."
              "All customer IDs must start with 'CUST-'"
          )
        }
      })

    # If no match is found, return a structured error response
    return json.dumps({
      "error": {
        "type": "business",
        "retryable": False,
        "message": (
            f"Customer ID '{query}' is was not found."
            "Please check the name, email, or customer ID and try again."
        )
      }
    })

@mcp.tool()
def lookup_order(order_id: str, session_state: dict) -> str:
    """
    Fetch an order using its order ID.
    Returns: Full order info, including: Status, items, shipping info, estimated delivery dates, notes.
    When to use: Look up an order when you already have its order ID
    When not to use: Find orders for a customer -> Use get_customer instead

    Args:
       order_id: The order ID to look up.
                 Must be ORD-NNNN, e.g. "ORD-1234".
                 Order will only be returned for an exact match.
    """

    # Normalize input (strip spaces + standardize casing)
    order_id = order_id.strip().upper()

    if (not order_id.startswith('ORD-')):
      return json.dumps({
        "error": {
          "type": "validation",
          "retryable": False,
          "message": (
              f"Order ID '{order_id}' is invalid."
              "All order IDs must start with 'ORD-'"
          )
        }
      })

    # Check if the order exists in the dataset
    if order_id in ORDERS:
        # Return the order details as a JSON string
        return json.dumps(ORDERS[order_id])

    # Return a structured error if the order is not found
    return json.dumps({
      "error": {
        "type": "business",
        "retryable": False,
        "message": (
            f"Order ID '{order_id}' not found."
            "Ask the customer to specify a valid order ID."
            "Double check their invoice."
        )
      }
    })

@mcp.tool()
def process_refund(customer_id: str, order_id: str, amount: float,
                   session_state: dict) -> str:
    """
    Process refund on an order, gated to run only if customer has been verified.
    Returns: Refund object, including order ID, status, and message.
    When to use: To initiate a refund attempt.
    When not to use: When have not yet verified the customer details.

    Args:
       customer_id: The customer ID of the verified customer
       order_id: The order ID of the order that should be refunded
       amount: The total value of the refund request
    """

    # Check 1: Has ID verification happened?
    if not session_state.get("verified_customer_id"):
        return json.dumps({
            "error": {
                "type": "permission",
                "retryable": False,
                "message": "Cannot process refund before customer identify is verified. Call get_customer first.",
            }
        })
    # Check 2: Does customer ID match?
    if session_state["verified_customer_id"] != customer_id:
        return json.dumps({
            "error": {
                "type": "permission",
                "retryable": False,
                "message": (
                    f"Customer ID mismatch.",
                    f"You are verified as {session_state['verified_customer_id']}, ",
                    f"but request for refund is for {customer_id}. "
                ),
            }
        })
    # Check 3: Does order exist?
    if (order_id not in ORDERS):
        return json.dumps({
            "error": {
                "type": "validation",
                "retryable": False,
                "message": f"Order {order_id} not found. Verify if order ID is correct before proceeding.",
            }
        })
    # Check 4: Does order belong to this verified customer?
    order = ORDERS[order_id]
    if (order["customer_id"] != session_state["verified_customer_id"]):
        return json.dumps({
            "error": {
                "type": "validation",
                "retryable": False,
                "message": f"Order {order_id} does not belong to customer {session_state['verified_customer_id']}. Verify if both customer ID and order ID are correct before proceeding.",
            }
        })
    # Process the refund
    return json.dumps({
        "success": True,
        "refund_id": "REF-" + order_id.split("-")[1],
        "customer_id": customer_id,
        "order_id": order_id,
        "amount": amount,
        "status": "initiated",
        "message": (
            f"Refund of ${amount:.2f} for order {order_id} has been initiated. "
            "Funds will return to the original payment method within 3-5 business days."
        )
    })


if __name__ == "__main__":
    mcp.run(transport="stdio")
