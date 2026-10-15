from loyalpet.events.webhook_utils import send_rename_notification


def notify_rename(doc, method, old_name, new_name, merge=False):
	"""autoname بتاع Item Group مبني على item_group_name (field:)، فأي تعديل
	للاسم من الديسك بيتحول لعملية rename_doc مش save عادي، وده مابيفعّلش
	ويب هوك on_update خالص (rename_doc بيشغّل before_rename/after_rename بس).
	بنبعت إشعار فيه الاسمين (قديم/جديد) عشان لارافيل يعمل rename حقيقي
	بدل ما يضيف سجل جديد ويسيب المنتجات مرتبطة بالاسم القديم."""
	send_rename_notification("Item Group", old_name, new_name)
