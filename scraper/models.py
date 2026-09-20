from django.db import models

class Product(models.Model):
    product_id = models.CharField(max_length=50, primary_key=True, help_text="Last 3 characters trimmed from p.title-sku")
    product_title = models.CharField(max_length=255)
    raw_sku = models.CharField(max_length=255, null=True, blank=True)
    price = models.IntegerField(null=True, blank=True, help_text="Scraped integer product price")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product_id} - {self.product_title}"

    class Meta:
        ordering = ['product_id']


class TrackedProduct(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, primary_key=True, related_name='tracked_info')
    tracked_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Tracked: {self.product.product_id} - {self.product.product_title}"

    class Meta:
        ordering = ['-tracked_at']


class PriceHistory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='price_history')
    price = models.IntegerField(help_text="Fetched product price")
    fetched_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when price was fetched")

    def __str__(self):
        return f"{self.product.product_id} - Rs. {self.price} at {self.fetched_at}"


    class Meta:
        db_table = 'price_history'
        ordering = ['-fetched_at']

