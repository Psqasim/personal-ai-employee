---
type: odoo_invoice
draft_id: MANUAL_Muhammad_Qasim_1771512067637
action: create_draft_invoice
status: pending
customer: Tayyab
amount: 10.00
currency: USD
description: For party
source_email_id: manual
source_email_from: muhammadqasim0326@gmail.com
created: 2026-02-19T14:41:07.641Z
mcp_server: odoo-mcp
---

## Odoo Invoice Draft

**Customer:** Tayyab
**Amount:** USD 10.00
**Description:** For party

---

*Created manually via dashboard by Muhammad Qasim on 2026-02-19T14:41:07.641Z*


---
**FAILED**: <Fault 1: 'Traceback (most recent call last):\n  File "/home/odoo/src/odoo/saas-19.1/addons/rpc/controllers/xmlrpc.py", line 163, in xmlrpc_2\n    response = self._xmlrpc(service)\n               ^^^^^^^^^^^^^^^^^^^^^\n  File "/home/odoo/src/custom/trial/saas_trial/controllers/main.py", line 467, in _xmlrpc\n    res = super()._xmlrpc(service)\n          ^^^^^^^^^^^^^^^^^^^^^^^^\n  File "/home/odoo/src/odoo/saas-19.1/addons/rpc/controllers/xmlrpc.py", line 135, in _xmlrpc\n    result = dispatch_rpc(service, method, params)\n             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File "/home/odoo/src/odoo/saas-19.1/odoo/http.py", line 466, in dispatch_rpc\n    return dispatch(method, params)\n           ^^^^^^^^^^^^^^^^^^^^^^^^\n  File "/home/odoo/src/odoo/saas-19.1/odoo/service/model.py", line 91, in dispatch\n    res = execute_cr(cr, uid, model, method_, args, kw)\n          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File "/home/odoo/src/odoo/saas-19.1/odoo/service/model.py", line 108, in execute_cr\n    result = http.retrying(partial(call_kw, recs, method, args, kw), env)\n             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File "/home/odoo/src/odoo/saas-19.1/odoo/http.py", line 509, in retrying\n    result = func()\n             ^^^^^^\n  File "/home/odoo/src/odoo/saas-19.1/odoo/service/model.py", line 56, in call_kw\n    result = method(recs, *args, **kwargs)\n             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File "/home/odoo/src/odoo/saas-19.1/odoo/orm/decorators.py", line 365, in create\n    return method(self, vals_list)\n           ^^^^^^^^^^^^^^^^^^^^^^^\n  File "/home/odoo/src/odoo/saas-19.1/addons/account/models/account_move.py", line 3842, in create\n    moves = super().create(vals_list)\n            ^^^^^^^^^^^^^^^^^^^^^^^^^\n  File "/home/odoo/src/odoo/saas-19.1/odoo/orm/decorators.py", line 365, in create\n    return method(self, vals_list)\n           ^^^^^^^^^^^^^^^^^^^^^^^\n  File "/home/odoo/src/odoo/saas-19.1/addons/mail/models/mail_thread.py", line 339, in create\n    threads = super(MailThread, self).create(vals_list)\n              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File "/home/odoo/src/odoo/saas-19.1/odoo/orm/decorators.py", line 365, in create\n    return method(self, vals_list)\n           ^^^^^^^^^^^^^^^^^^^^^^^\n  File "/home/odoo/src/odoo/saas-19.1/odoo/orm/models.py", line 4021, in create\n    records = self._create(data_list)\n              ^^^^^^^^^^^^^^^^^^^^^^^\n  File "/home/odoo/src/enterprise/saas-19.1/ai_fields/models/models.py", line 43, in _create\n    return super()._create(data_list)\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File "/home/odoo/src/odoo/saas-19.1/odoo/orm/models.py", line 4201, in _create\n    cr.execute(SQL(\n  File "/home/odoo/src/odoo/saas-19.1/odoo/sql_db.py", line 431, in execute\n    self._obj.execute(query, params)\npsycopg2.errors.DatatypeMismatch: column "partner_id" is of type integer but expression is of type integer[]\nLINE 1: ... 1.0, \'2026-02-19\'::date, NULL, 8, \'out_invoice\', ARRAY[12],...\n                                                             ^\nHINT:  You will need to rewrite or cast the expression.\n\n'>
**At**: 2026-02-19T19:48:52.266494
