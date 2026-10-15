from loyalpet.events.webhook_utils import notify_webhook


def notify_rename(doc, method, old_name, new_name, merge=False):
	"""autoname بتاع Item Group مبني على item_group_name (field:)، فأي تعديل
	للاسم من الديسك بيتحول لعملية rename_doc مش save عادي، وده مابيفعّلش
	ويب هوك on_update خالص (rename_doc بيشغّل before_rename/after_rename بس)."""
	notify_webhook(doc, "LoyalPet Item Group Sync")
