from datetime import date, datetime
from typing import Any, Dict, List, override

from django.urls import reverse
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.admin.views.reports.base import ReportView

from servicerequests.models import ServiceRequest


class TaxYearServiceRequestReport(ReportView):
    """
    A report that shows the number of pending and rejected service requests by tax year.
    A tax year is defined as April 1st of a given year to March 31st of the following year.
    """
    # template_name = "wagtailadmin/reports/base_report.html"
    results_template_name = "servicerequests/admin/servicerequest_report_result.html"
    title = "Demandes de Services par Année Fiscale"
    page_title = "Demandes de Services par Année Fiscale"
    header_icon = "form"
    list_export = ("tax_year", "tax_year_display", "rejected_count", "pending_count", "accepted_count", "total_count")

    @override
    def get_queryset(self) -> List[Dict[str, Any]]:
        """
        Get the data for the report, grouped by tax year.

        Returns:
            A list of dictionaries, each representing a tax year with counts of pending and rejected requests.
        """
        # Get all service requests
        service_requests = ServiceRequest.objects.all() # Type is QuerySet[ServiceRequest], but somehow adding type hint gives error

        service_requests_ord = service_requests.order_by('created_at')
        earliest_request = service_requests_ord.first()
        latest_request = service_requests_ord.last()


        if not earliest_request or not latest_request:
            return []

        earliest_date: datetime = earliest_request.created_at
        latest_date: datetime = latest_request.created_at

        # Determine the range of tax years to include
        earliest_year: int = earliest_date.year
        if earliest_date.month < 4:
            earliest_year -= 1

        latest_year: int = latest_date.year
        if latest_date.month > 3: # Then the last tax year is latest year --> latest year + 1
            latest_year += 1

        # Generate the report data for each tax year
        report_data: List[Dict[str, Any]] = []

        for year in range(earliest_year, latest_year):
            # Define the tax year period, which is April 1st of current year to March 31st of the following year
            tax_year_start: date = date(year, 4, 1)
            # Important: tax_year_end is effectively checking if the request was created before and during March 31st.
            # Despite the code showing month April 1st, the only time a user request made in April 1st would be categorized into the preview tax year
            # Is if the request was made at April 1st exactly at 0h0m0s0ms. Which will be so rare to happen.
            tax_year_end: date = date(year + 1, 4, 1)

            # Count pending and rejected requests for this tax year
            pending_count = service_requests_ord.filter(
                status="pending",
                created_at__gt=tax_year_start,
                created_at__lte=tax_year_end
            ).count()

            rejected_count = service_requests_ord.filter(
                status="rejected",
                created_at__gt=tax_year_start,
                created_at__lte=tax_year_end
            ).count()

            accepted_count = service_requests_ord.filter(
                status="accepted",
                created_at__gt=tax_year_start,
                created_at__lte=tax_year_end
            ).count()

            total_count = service_requests_ord.filter(
                created_at__gt=tax_year_start,
                created_at__lte=tax_year_end
            ).count()

            # Only include tax years with at least one request
            if pending_count > 0 or rejected_count > 0:
                report_data.append({
                    'tax_year': year,
                    'tax_year_display': f"1 avril {year} - 31 mars {year + 1}",
                    'rejected_count': rejected_count,
                    'pending_count': pending_count,
                    'accepted_count': accepted_count, 
                    'total_count': total_count,   
                })

        # Sort by tax year (most recent first)
        report_data.sort(key=lambda x: x['tax_year'], reverse=True)

        # return ServiceRequest.objects.filter(status="pending")
        return report_data


@hooks.register('register_reports_menu_item')
def register_service_request_report_menu_item() -> MenuItem:
    """
    Register the service request report in the reports menu.

    Returns:
        A MenuItem for the service request report.
    """
    return MenuItem(
        'Demandes de Services',
        reverse('service_request_report'),
        icon_name='form',
        order=1000000 # Last item in the menu items
    )
