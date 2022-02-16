import frappe
from helpdesk.helpdesk.doctype.ticket.ticket import get_all_conversations, create_communication_via_agent
import json

@frappe.whitelist(allow_guest=True)
def get_tickets():
	all_tickets = frappe.db.sql("""
		SELECT
			ticket.subject,
			ticket.modified,
			ticket.status,
			ticket.name,
			ticket.ticket_type,
			contact.name as contact
		FROM `tabTicket` ticket
		LEFT JOIN `tabContact` contact
		ON ticket.contact = contact.name
		ORDER BY ticket.creation desc
	""", as_dict=1)

	for ticket in all_tickets:
		ticket['assignees'] = get_agent_assigned_to_ticket(ticket['name'])

	return all_tickets

@frappe.whitelist(allow_guest=True)
def get_ticket(ticket_id):
	ticket_doc = frappe.get_doc("Ticket", ticket_id)
	ticket_doc = ticket_doc.__dict__
	ticket_doc["assignees"] = get_agent_assigned_to_ticket(ticket_id)
	return ticket_doc

def get_agent_assigned_to_ticket(ticket_id):
	agents = []
	ticket_doc = frappe.get_doc("Ticket", ticket_id)
	if ticket_doc._assign:
		assignees = json.loads(ticket_doc._assign)
		for assignee in assignees:
			agent = frappe.get_doc("Agent", assignee)
			agent = agent.__dict__
			agent['image'] = frappe.get_value("User", agent["name"], "user_image")
			agents.append(agent)
	return agents

@frappe.whitelist(allow_guest=True)
def assign_ticket_to_agent(ticket_id, agent_id=None):
	if ticket_id:
		ticket_doc = frappe.get_doc("Ticket", ticket_id)
		ticket_doc.assign_agent(agent_id)
		frappe.db.commit()

@frappe.whitelist(allow_guest=True)
def assign_ticket_type(ticket_id, type):
	if ticket_id:
		ticket_doc = frappe.get_doc("Ticket", ticket_id)
		ticket_doc.ticket_type = type
		ticket_doc.save()

@frappe.whitelist(allow_guest=True)
def assign_ticket_status(ticket_id, status):
	if ticket_id:
		ticket_doc = frappe.get_doc("Ticket", ticket_id)
		ticket_doc.status = status
		ticket_doc.save()

@frappe.whitelist(allow_guest=True)
def get_all_ticket_types():
	return frappe.get_all("Ticket Type", pluck="name")

#TODO: the code can be made better
@frappe.whitelist(allow_guest=True)
def get_all_ticket_statuses():
	statuses = []
	ticket_doctype = frappe.get_doc("DocType", "Ticket")
	for field in ticket_doctype.fields:
		doc_field = frappe.get_doc("DocField", field.__dict__["name"])
		if doc_field.label == "Status":
			statuses = doc_field.options.split("\n")
	return statuses

@frappe.whitelist(allow_guest=True)
def get_contact(ticket_id):
	contact_id = frappe.get_value("Ticket", ticket_id, "contact")
	contact_doc = frappe.get_doc("Contact", contact_id)

	return contact_doc

@frappe.whitelist(allow_guest=True)
def get_conversations(ticket_id):
	return get_all_conversations(ticket_id)

@frappe.whitelist(allow_guest=True)
def submit_conversation(ticket_id, message):
	return create_communication_via_agent(ticket_id, message)

@frappe.whitelist(allow_guest=True)
def get_other_tickets_of_contact(ticket_id):
	contact = frappe.get_value("Ticket", ticket_id, "raised_by")
	tickets = frappe.get_all("Ticket", filters={"raised_by": contact, "name": ["!=", ticket_id]}, fields=['name', 'subject'])
	return tickets