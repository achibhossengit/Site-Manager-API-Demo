from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from .models import CustomUser


@receiver(pre_save, sender=CustomUser)
def delete_old_profile_image(sender, instance, **kwargs):    
    if not instance.pk:
        return
    try:
        old_instance = CustomUser.objects.get(pk=instance.pk)
    except CustomUser.DoesNotExist:
        return

    old_image = old_instance.profile_image
    new_image = instance.profile_image
        
    if old_image and old_image != new_image:
        old_image.delete(save=False)

            
@receiver(post_delete, sender=CustomUser)
def delete_profile_image_on_delete(sender, instance, **kwargs):
    if instance.profile_image:
        instance.profile_image.delete()
