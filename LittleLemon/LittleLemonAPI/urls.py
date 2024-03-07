from django.urls import path 
from . import views 
  
urlpatterns = [ 
    path('menu-items/', views.menu_items),
    path('menu-items/<int:id>', views.single_item),
    path('cart/menu-items/', views.cart_item),
    path('orders/', views.orders),
    path('orders/<int:id>', views.single_order),
    path('groups/manager/users/', views.user_managers),
    path('groups/manager/users/<int:id>', views.del_from_manager),
    path('groups/delivery-crew/users/', views.user_delivery_crew),
    path('groups/delivery-crew/users/<int:id>', views.del_from_delivery_crew),
] 