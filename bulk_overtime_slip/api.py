import frappe


@frappe.whitelist()
def get_employees(docname):
    """
    Populate Employee table.
    """

    tool = frappe.get_doc("Bulk Overtime Slip Tool", docname)

    return _populate_employee_table(tool)


def _populate_employee_table(tool):

    filters = {
        "status": "Active",
        "company": tool.company,
    }

    if tool.branch:
        filters["branch"] = tool.branch

    if tool.department:
        filters["department"] = tool.department

    if tool.designation:
        filters["designation"] = tool.designation

    if tool.employment_type:
        filters["employment_type"] = tool.employment_type

    if tool.employee_grade:
        filters["grade"] = tool.employee_grade

    employees = frappe.get_all(
        "Employee",
        filters=filters,
        fields=[
            "name",
            "employee_name",
            "department"
        ],
        order_by="name"
    )

    tool.set("employees", [])
    existing_slips = {}

    slips = frappe.get_all(
        "Overtime Slip",
        filters={
            "company": tool.company,
            "start_date": tool.from_date,
            "end_date": tool.to_date,
            "docstatus": ["!=", 2],
        },
        fields=["name", "employee"],
    )

    for slip in slips:
        existing_slips[slip.employee] = slip.name

    already_exists = 0
    selected = 0

    for emp in employees:

        row = tool.append("employees", {})

        row.employee = emp.name
        row.employee_name = emp.employee_name
        row.department = emp.department

        existing_slip = existing_slips.get(emp.name)

        if existing_slip:
            row.existing_slip = existing_slip

            if tool.skip_if_slip_exists:
                row.select = 0
                row.result = "Already Exists"
            else:
                row.select = 1
                row.result = ""

            already_exists += 1

        else:
            row.select = 1
            selected += 1

    # tool.employee_count = f"{len(employees)} employees listed"

    # tool.employee_count = (
    #     f"{len(employees)} Listed | "
    #     f"{selected} Selected | "
    #     f"{already_exists} Existing"
    # )

    tool.save(ignore_permissions=True)

    return len(employees)


@frappe.whitelist()
def create_overtime_slips(docname):
    """
    Start background job to create overtime slips.
    """

    frappe.enqueue(
        "bulk_overtime_slip.background_jobs.create_overtime_slips",
        queue="long",
        timeout=3600,
        docname=docname,
    )

    return {"status": "queued"}