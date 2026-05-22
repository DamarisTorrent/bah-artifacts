"""
Contractor Portal API - Invoice Client

A Python client for interacting with all invoice endpoints in the Contractor Portal API.
Supports OAuth 2.0 authentication, pagination, and all invoice operations.
"""

import requests
from typing import Optional, Dict, Any, List
from datetime import datetime
from urllib.parse import urljoin


class ContractorPortalInvoiceClient:
    """
    Client for interacting with the Contractor Portal API invoice endpoints.
    
    Base URL: https://api.contractor-portal.gov/v2
    
    Supports:
    - List invoices with filtering and pagination
    - Get individual invoice details
    - Create draft invoices
    - Update invoices (draft or rejected status only)
    - Submit invoices for review
    - Approve invoices (requires contracting_officer role)
    - Reject invoices with notes
    """
    
    BASE_URL = "https://api.contractor-portal.gov/v2"
    AUTH_ENDPOINT = "/auth/token"
    INVOICES_ENDPOINT = "/invoices"
    
    def __init__(self, client_id: str, client_secret: str, base_url: Optional[str] = None):
        """
        Initialize the invoice client.
        
        Args:
            client_id: OAuth 2.0 client ID
            client_secret: OAuth 2.0 client secret
            base_url: Optional custom base URL (defaults to production)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url or self.BASE_URL
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self.session = requests.Session()
    
    def _get_url(self, endpoint: str) -> str:
        """Construct full URL for an endpoint."""
        return urljoin(self.base_url, endpoint)
    
    def authenticate(self, scopes: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Obtain an OAuth 2.0 access token.
        
        Args:
            scopes: List of required scopes. Defaults to invoices:read and invoices:write
            
        Returns:
            Token response dictionary
            
        Raises:
            requests.HTTPError: If authentication fails
        """
        if scopes is None:
            scopes = ["invoices:read", "invoices:write"]
        
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": " ".join(scopes)
        }
        
        response = self.session.post(
            self._get_url(self.AUTH_ENDPOINT),
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()
        
        token_data = response.json()
        self.access_token = token_data["access_token"]
        
        # Calculate token expiration time
        expires_in = token_data.get("expires_in", 3600)
        self.token_expires_at = datetime.now().timestamp() + expires_in
        
        return token_data
    
    def _ensure_authenticated(self):
        """Ensure we have a valid access token, refreshing if necessary."""
        if not self.access_token or (
            self.token_expires_at and datetime.now().timestamp() >= self.token_expires_at - 60
        ):
            self.authenticate()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication token."""
        self._ensure_authenticated()
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle API response and raise appropriate errors.
        
        Args:
            response: requests Response object
            
        Returns:
            Parsed JSON response
            
        Raises:
            requests.HTTPError: For HTTP errors with detailed error information
        """
        try:
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            # Try to extract error details from response
            try:
                error_data = response.json()
                error_msg = f"API Error: {error_data.get('error', {}).get('message', str(e))}"
                raise requests.HTTPError(error_msg, response=response) from e
            except ValueError:
                raise e
    
    def list_invoices(
        self,
        task_order_id: Optional[str] = None,
        contractor_id: Optional[str] = None,
        status: Optional[str] = None,
        submitted_after: Optional[str] = None,
        page: Optional[int] = None,
        per_page: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        List invoices with optional filtering and pagination.
        
        Args:
            task_order_id: Filter by task order UUID
            contractor_id: Filter by contractor UUID
            status: Filter by invoice status (draft, submitted, under_review, approved, rejected, paid)
            submitted_after: Filter by submission date (ISO 8601 date format)
            page: Page number (1-indexed)
            per_page: Results per page
            
        Returns:
            Dictionary containing:
                - data: List of invoice objects
                - pagination: Pagination metadata (page, per_page, total, total_pages)
        """
        params = {}
        if task_order_id:
            params["task_order_id"] = task_order_id
        if contractor_id:
            params["contractor_id"] = contractor_id
        if status:
            params["status"] = status
        if submitted_after:
            params["submitted_after"] = submitted_after
        if page:
            params["page"] = page
        if per_page:
            params["per_page"] = per_page
        
        response = self.session.get(
            self._get_url(self.INVOICES_ENDPOINT),
            headers=self._get_headers(),
            params=params
        )
        
        return self._handle_response(response)
    
    def get_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """
        Get a single invoice by ID.
        
        Args:
            invoice_id: Invoice UUID
            
        Returns:
            Invoice object
        """
        response = self.session.get(
            self._get_url(f"{self.INVOICES_ENDPOINT}/{invoice_id}"),
            headers=self._get_headers()
        )
        
        return self._handle_response(response)
    
    def create_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new draft invoice.
        
        Creates a draft invoice. Set status to 'submitted' to officially submit it for review,
        or use the submit_invoice() method after creation.
        
        Args:
            invoice_data: Invoice object (omit id, created_at, updated_at)
                Required fields:
                    - invoice_number: string
                    - task_order_id: UUID string
                    - contractor_id: UUID string
                    - period_start: ISO 8601 date
                    - period_end: ISO 8601 date
                    - line_items: List of line item objects
                    - subtotal: number
                    - tax: number
                    - total: number
                Optional fields:
                    - status: string (defaults to 'draft')
                    - supporting_documents: List of URL strings
                    
        Returns:
            Created invoice object with status 201
        """
        response = self.session.post(
            self._get_url(self.INVOICES_ENDPOINT),
            headers=self._get_headers(),
            json=invoice_data
        )
        
        return self._handle_response(response)
    
    def update_invoice(self, invoice_id: str, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing invoice.
        
        Only allowed when invoice status is 'draft' or 'rejected'.
        
        Args:
            invoice_id: Invoice UUID
            invoice_data: Partial invoice object (only include fields to update)
            
        Returns:
            Updated invoice object
            
        Raises:
            requests.HTTPError: If invoice is not in draft or rejected status (409 Conflict)
        """
        response = self.session.patch(
            self._get_url(f"{self.INVOICES_ENDPOINT}/{invoice_id}"),
            headers=self._get_headers(),
            json=invoice_data
        )
        
        return self._handle_response(response)
    
    def submit_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """
        Submit a draft invoice for review.
        
        Transitions a 'draft' invoice to 'submitted' status. Validates that all required
        fields are present and that the total does not exceed the task order's remaining ceiling.
        
        Args:
            invoice_id: Invoice UUID
            
        Returns:
            Updated invoice object with submission_date set
            
        Raises:
            requests.HTTPError: 
                - 409 Conflict: If invoice is not in draft status
                - 422 Unprocessable Entity: If validation fails or ceiling exceeded
        """
        response = self.session.post(
            self._get_url(f"{self.INVOICES_ENDPOINT}/{invoice_id}/submit"),
            headers=self._get_headers()
        )
        
        return self._handle_response(response)
    
    def approve_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """
        Approve an invoice.
        
        Requires 'invoices:write' scope with the 'contracting_officer' role.
        Transitions invoice to 'approved' status.
        
        Args:
            invoice_id: Invoice UUID
            
        Returns:
            Updated invoice object with approved status
            
        Raises:
            requests.HTTPError:
                - 403 Forbidden: If user lacks contracting_officer role
                - 409 Conflict: If invoice is not in appropriate status for approval
        """
        response = self.session.post(
            self._get_url(f"{self.INVOICES_ENDPOINT}/{invoice_id}/approve"),
            headers=self._get_headers()
        )
        
        return self._handle_response(response)
    
    def reject_invoice(self, invoice_id: str, notes: str) -> Dict[str, Any]:
        """
        Reject an invoice with required notes.
        
        Transitions invoice to 'rejected' status. The notes field is required and will
        be stored as reviewer_notes.
        
        Args:
            invoice_id: Invoice UUID
            notes: Required rejection notes explaining why the invoice was rejected
            
        Returns:
            Updated invoice object with rejected status and reviewer_notes
            
        Raises:
            requests.HTTPError:
                - 400 Bad Request: If notes are missing or empty
                - 409 Conflict: If invoice is not in appropriate status for rejection
        """
        response = self.session.post(
            self._get_url(f"{self.INVOICES_ENDPOINT}/{invoice_id}/reject"),
            headers=self._get_headers(),
            json={"notes": notes}
        )
        
        return self._handle_response(response)
    
    def list_all_invoices(
        self,
        task_order_id: Optional[str] = None,
        contractor_id: Optional[str] = None,
        status: Optional[str] = None,
        submitted_after: Optional[str] = None,
        per_page: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all invoices across all pages.
        
        Automatically handles pagination to retrieve all matching invoices.
        
        Args:
            task_order_id: Filter by task order UUID
            contractor_id: Filter by contractor UUID
            status: Filter by invoice status
            submitted_after: Filter by submission date (ISO 8601 date format)
            per_page: Results per page (max 100)
            
        Returns:
            List of all invoice objects matching the filters
        """
        all_invoices = []
        page = 1
        
        while True:
            response = self.list_invoices(
                task_order_id=task_order_id,
                contractor_id=contractor_id,
                status=status,
                submitted_after=submitted_after,
                page=page,
                per_page=per_page
            )
            
            all_invoices.extend(response["data"])
            
            pagination = response.get("pagination", {})
            if page >= pagination.get("total_pages", 1):
                break
            
            page += 1
        
        return all_invoices


# Example usage
if __name__ == "__main__":
    # Initialize the client
    client = ContractorPortalInvoiceClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET"
    )
    
    # Authenticate (happens automatically on first request, but can be called explicitly)
    client.authenticate()
    
    # List all invoices
    invoices = client.list_invoices(status="submitted", per_page=20)
    print(f"Found {invoices['pagination']['total']} submitted invoices")
    
    # Get a specific invoice
    invoice = client.get_invoice("invoice-uuid-here")
    print(f"Invoice {invoice['invoice_number']}: ${invoice['total']}")
    
    # Create a new draft invoice
    new_invoice = client.create_invoice({
        "invoice_number": "INV-2026-001",
        "task_order_id": "task-order-uuid",
        "contractor_id": "contractor-uuid",
        "period_start": "2026-05-01",
        "period_end": "2026-05-31",
        "line_items": [
            {
                "clin_number": "0001",
                "description": "Software Development Services",
                "hours": 160,
                "rate": 125.00,
                "amount": 20000.00
            }
        ],
        "subtotal": 20000.00,
        "tax": 0.00,
        "total": 20000.00,
        "supporting_documents": ["https://example.com/timesheet.pdf"]
    })
    print(f"Created invoice: {new_invoice['id']}")
    
    # Update the invoice
    updated_invoice = client.update_invoice(
        new_invoice['id'],
        {"tax": 1600.00, "total": 21600.00}
    )
    
    # Submit the invoice for review
    submitted_invoice = client.submit_invoice(new_invoice['id'])
    print(f"Invoice submitted on: {submitted_invoice['submission_date']}")
    
    # Approve an invoice (requires contracting_officer role)
    try:
        approved_invoice = client.approve_invoice(new_invoice['id'])
        print(f"Invoice approved: {approved_invoice['status']}")
    except requests.HTTPError as e:
        print(f"Could not approve: {e}")
    
    # Reject an invoice with notes
    rejected_invoice = client.reject_invoice(
        new_invoice['id'],
        notes="Missing timesheet attachments for period 2026-05-01 to 2026-05-15"
    )
    print(f"Invoice rejected: {rejected_invoice['reviewer_notes']}")
    
    # Get all invoices for a contractor (handles pagination automatically)
    all_contractor_invoices = client.list_all_invoices(
        contractor_id="contractor-uuid",
        status="approved"
    )
    print(f"Total approved invoices for contractor: {len(all_contractor_invoices)}")