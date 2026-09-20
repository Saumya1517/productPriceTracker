from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db import connection
from .models import Product

def search_api(request):
    """
    Search endpoint that accepts a query string,
    executes a SQL query using LIKE operator for partial and full search,
    and returns product_id along with product details.
    """
    query = request.GET.get('q', '').strip()
    
    if not query:
        # Return recent products or empty list if no query
        products = list(Product.objects.all().values('product_id', 'product_title', 'raw_sku')[:20])
        return JsonResponse({
            'success': True,
            'query': '',
            'count': len(products),
            'results': products
        })

    # Execute raw SQL with LIKE operator specifically on product_title
    like_pattern = f"%{query}%"
    
    # Check DB vendor for exact LIKE / ILIKE syntax (ILIKE for PostgreSQL, LIKE for SQLite)
    db_vendor = connection.vendor
    like_op = "ILIKE" if db_vendor == 'postgresql' else "LIKE"
    
    sql_query = f"""
        SELECT product_id, product_title, raw_sku, created_at, updated_at
        FROM scraper_product
        WHERE product_title {like_op} %s
        ORDER BY 
            CASE 
                WHEN product_title = %s THEN 1
                WHEN product_title {like_op} %s THEN 2
                ELSE 3
            END,
            product_title ASC
        LIMIT 50;
    """
    params = [like_pattern, query, f"{query}%"]

    results = []
    with connection.cursor() as cursor:
        cursor.execute(sql_query, params)
        columns = [col[0] for col in cursor.description]
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            results.append({
                'product_id': row_dict['product_id'],
                'product_title': row_dict['product_title'],
                'raw_sku': row_dict.get('raw_sku', ''),
            })

    return JsonResponse({
        'success': True,
        'query': query,
        'count': len(results),
        'results': results
    })


from django.views.decorators.csrf import csrf_exempt
from .models import Product, TrackedProduct

# ... existing code ...

def search_view(request):
    """Render Search Frontend"""
    return render(request, 'scraper/search.html')


def dashboard_view(request, product_id):
    """Render Dashboard Frontend for /dashboard/{product_id}"""
    product = get_object_or_404(Product, product_id=product_id)
    
    # Check if this product is tracked
    is_tracked = TrackedProduct.objects.filter(product=product).exists()
    
    # Related products
    related_products = Product.objects.exclude(product_id=product_id)[:4]

    context = {
        'product': product,
        'product_id': product.product_id,
        'product_title': product.product_title,
        'raw_sku': product.raw_sku,
        'created_at': product.created_at,
        'updated_at': product.updated_at,
        'is_tracked': is_tracked,
        'related_products': related_products,
    }
    return render(request, 'scraper/dashboard.html', context)


@csrf_exempt
def track_product_api(request, product_id):
    """
    API to add or toggle product in the TrackedProduct database table.
    """
    if request.method not in ['POST', 'GET']:
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    product = get_object_or_404(Product, product_id=product_id)
    
    # Check if already tracked
    tracked_obj = TrackedProduct.objects.filter(product=product).first()
    
    if tracked_obj:
        # If action is 'add' or GET, keep tracked. If toggle, we can either keep or remove
        action = request.GET.get('action', 'toggle')
        if action == 'toggle':
            tracked_obj.delete()
            is_tracked = False
            message = "Product removed from tracking."
        else:
            is_tracked = True
            message = "Product is already tracked."
    else:
        TrackedProduct.objects.create(product=product)
        is_tracked = True
        message = "Product successfully added to tracked products!"

    return JsonResponse({
        'success': True,
        'product_id': product_id,
        'product_title': product.product_title,
        'is_tracked': is_tracked,
        'message': message,
    })
