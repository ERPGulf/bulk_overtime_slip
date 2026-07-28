import frappe
from frappe import _


def create_overtime_slips(docname):
    """Background job to create Overtime Slips."""

    tool = frappe.get_doc("Bulk Overtime Slip Tool", docname)

    for row in tool.employees:

        if not row.select:
            continue

        try:

            # Skip if another slip was created 

            existing = frappe.db.exists(
                "Overtime Slip",
                {
                    "employee": row.employee,
                    "company": tool.company,
                    "docstatus": ["!=", 2],
                    "start_date": ["<=", tool.to_date],
                    "end_date": [">=", tool.from_date],
                },
            )

            if existing:
                row.result = "Skipped"
                row.remarks = _("Overtime Slip already exists.")
                row.existing_slip = existing
                row.created_slip = ""

                tool.save(ignore_permissions=True)
                frappe.db.commit()
                continue

            # Create Overtime Slip
            slip = frappe.new_doc("Overtime Slip")

            slip.company = tool.company
            slip.employee = row.employee
            slip.posting_date = tool.posting_date

            if tool.respect_payroll_frequency:
                slip.get_frequency_and_dates()
            else:
                slip.start_date = tool.from_date
                slip.end_date = tool.to_date

            # Creates overtime_details and saves the document

            slip.get_emp_and_overtime_details()

            # Skip Zero Overtime

            total_overtime = sum(
                frappe.utils.flt(d.overtime_duration)
                for d in (slip.overtime_details or [])
            )

            if tool.skip_zero_overtime and total_overtime <= 0:

                row.result = "Skipped"
                row.remarks = _("Skipped - Zero Overtime")

                if slip.name:
                    frappe.delete_doc(
                        "Overtime Slip",
                        slip.name,
                        ignore_permissions=True,
                        force=True,
                    )

                tool.save(ignore_permissions=True)
                frappe.db.commit()

                continue

            # Submit After Creation

            if tool.submit_after_creation:
                slip = frappe.get_doc("Overtime Slip", slip.name)
                slip.submit()
                row.result = "Submitted"
            else:
                row.result = "Created"

            row.created_slip = slip.name
            row.existing_slip = ""
            row.remarks = ""

        # except Exception:

        #     row.result = "Failed"
        #     row.remarks = frappe.get_traceback()

        #     frappe.log_error(
        #         frappe.get_traceback(),
        #         _("Bulk Overtime Slip Error"),
        #     )
        except frappe.MandatoryError as e:

            if (
                tool.skip_zero_overtime
                and "overtime_details" in str(e)
            ):
                row.result = "Skipped"
                row.remarks = _("Skipped - Zero Overtime")
            else:
                row.result = "Failed"
                row.remarks = str(e)

        except Exception:
            row.result = "Failed"
            row.remarks = frappe.get_traceback()

            frappe.log_error(
                frappe.get_traceback(),
                _("Bulk Overtime Slip Error"),
            )

        tool.save(ignore_permissions=True)
        frappe.db.commit()