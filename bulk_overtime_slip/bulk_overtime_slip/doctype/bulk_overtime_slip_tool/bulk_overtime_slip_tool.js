frappe.ui.form.on("Bulk Overtime Slip Tool", {

    refresh(frm) {

        // Only show after the document has been saved
        if (!frm.is_new()) {

            frm.add_custom_button(__("Create Overtime Slips"), () => {
                frm.trigger("create_overtime_slips");
            });
        }
    },

    get_employees(frm) {

        if (frm.is_new()) {
            frappe.msgprint(__("Please save the document first."));
            return;
        }

        frappe.call({
            method: "bulk_overtime_slip.api.get_employees",
            args: {
                docname: frm.doc.name
            },
            freeze: true,
            freeze_message: __("Getting Employees..."),
            callback() {
                frm.reload_doc();
            }
        });
    },

    create_overtime_slips(frm) {

    if (!frm.doc.company) {
        frappe.throw(__("Please select Company."));
    }

    if (!frm.doc.from_date || !frm.doc.to_date) {
        frappe.throw(__("Please select the date range."));
    }

    let selected = (frm.doc.employees || []).filter(d => d.select);

    if (!selected.length) {
        frappe.throw(__("Please select at least one employee."));
    }

    frappe.confirm(
        __("Create Overtime Slips for {0} employees?", [selected.length]),
        () => {

            frappe.call({
                method: "bulk_overtime_slip.api.create_overtime_slips",
                args: {
                    docname: frm.doc.name
                },
                freeze: true,
                freeze_message: __("Starting Background Job..."),
                callback(r) {

                    frappe.msgprint(__("Background job started."));

                    frm.reload_doc();
                }
            });

        }
    );
}

});