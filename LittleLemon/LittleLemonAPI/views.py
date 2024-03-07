from email.policy import default
from os import name
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import MenuItem, Cart, Order, OrderItem
from .serializers import MenuItemSerializer, CategorySerializer, CartSerializer, OrderSerializer, OrderItemSerializer
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from django.shortcuts import get_object_or_404
from rest_framework import status
from django.core.paginator import Paginator, EmptyPage
from decimal import Decimal
from django.contrib.auth.models import User, Group
from rest_framework.throttling import AnonRateThrottle
from rest_framework.throttling import UserRateThrottle

    
@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def menu_items(request):
    if(request.method=='GET'):
        items = MenuItem.objects.select_related('category').all()
        category_name = request.query_params.get('category')
        to_price = request.query_params.get('to_price')
        search = request.query_params.get('search')
        ordering = request.query_params.get('ordering')
        perpage = request.query_params.get('perpage',default=2)
        page = request.query_params.get('page',default=1)
        if category_name:
            items = items.filter(category__title=category_name)
        if to_price:
            items = items.filter(price=to_price)
        if search:
            items = items.filter(title__contains=search)
        if ordering:
            order_fields = ordering.split(",")
            items = items.order_by(*order_fields)
            
        paginator = Paginator(items,per_page=perpage)
        try:
            items = paginator.page(number=page)
        except EmptyPage:
            items = []
        serialized_item = MenuItemSerializer(items, many=True)
        return Response(serialized_item.data)
    elif (request.method=='POST'):
        if (request.user.groups.filter(name='Manager').exists()):
            serialized_item = MenuItemSerializer(data=request.data)
            serialized_item.is_valid(raise_exception=True)
            serialized_item.save()
            return Response(serialized_item.data, status.HTTP_201_CREATED)
        else: 
            return Response({"message": "You are not authorized"}, 403)


@api_view(['GET','PUT','PATCH','DELETE'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def single_item(request, id):
    if request.method == 'GET':
        item = get_object_or_404(MenuItem, pk=id)
        serialized_item = MenuItemSerializer(item)
        return Response(serialized_item.data)
    elif (request.method == 'PUT' or request.method == 'PATCH'):
        if (request.user.groups.filter(name='Manager').exists()):
            item = get_object_or_404(MenuItem, pk=id)
            
            serialized_item = MenuItemSerializer(item, data=request.data, partial = True)
            
            serialized_item.is_valid(raise_exception=True)
            serialized_item.save()
            
            return Response(serialized_item.data, status.HTTP_201_CREATED)
        else:
            return Response({"message": "You are not authorized"}, 403)
    elif request.method == 'DELETE':
        if (request.user.groups.filter(name='Manager').exists()):
            item = get_object_or_404(MenuItem, pk=id)
            item.delete()
            return Response(status.HTTP_200_OK)    
        else:
            return Response({"message": "You are not authorized"}, 403)
        

@api_view(['GET','POST','DELETE'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def cart_item(request):
    if request.method == 'GET':
        item = Cart.objects.filter(user=request.user)
        serialized_item = CartSerializer(item, many=True)
        return Response(serialized_item.data)
    elif request.method == 'POST':
        serialized_item = CartSerializer( data={
            'user': request.user.id,
            'menuitem_id': request.data['menuitem_id'], 
            'quantity': request.data['quantity']
            } )
        serialized_item.is_valid(raise_exception=True)
        serialized_item.save()
        return Response(serialized_item.data, status.HTTP_201_CREATED)
    
    elif request.method == 'DELETE': 
        item = Cart.objects.filter(user=request.user)

        item.delete()
        return Response(status.HTTP_200_OK)   


@api_view(['GET','POST','DELETE'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def orders(request):
    if request.method == 'GET':
        if (request.user.groups.filter(name='Manager').exists()):
            orders = Order.objects.all()
            order_items = OrderItem.objects.all()
            
            serialized_order = OrderSerializer(orders, many=True)
            serialized_order_items = OrderItemSerializer(order_items, many=True)
            response_data = {
                'orders': serialized_order.data,
                'order_items': serialized_order_items.data
            }
            return Response(response_data)
        
        
        elif (request.user.groups.filter(name='Delivery Crew').exists()):
            orders = Order.objects.filter(delivery_crew=request.user)

            serialized_orders = OrderSerializer(orders, many=True)
            serialized_items = []
            for order in serialized_orders.data:
                order_items = OrderItem.objects.filter(order=order['id'])
                serialized_order_items = OrderItemSerializer(order_items, many=True)
                serialized_items.append(serialized_order_items.data)
            
            response_data = {
                'order': serialized_orders.data,
                'order_items': serialized_items
            }
            return Response(response_data)
            

        else:
            orders = Order.objects.filter(user=request.user)
            
            serialized_orders = OrderSerializer(orders, many=True)
            serialized_items = []
            for order in serialized_orders.data:
                order_items = OrderItem.objects.filter(order=order['id'])
                serialized_order_items = OrderItemSerializer(order_items, many=True)
                serialized_items.append(serialized_order_items.data)
            
            response_data = {
                'order': serialized_orders.data,
                'order_items': serialized_items
            }
            return Response(response_data)
            
    elif request.method == 'POST':

        cart_items = Cart.objects.filter(user=request.user)
        if cart_items:
            total = Decimal(0.00)
            for cart_item in cart_items:
                total += cart_item.price
            
            serialized_order = OrderSerializer(
                data={
                    'user': request.user.id,
                    'total': total,
                    'date': '2024-02-09',
                },
                many = False
            )
            serialized_order.is_valid(raise_exception=True)

            order = serialized_order.save()


            serialized_items = []
            
            for cart_item in cart_items:
        
                serialized_orderitems = OrderItemSerializer(
                    data={
                        'order': order.id,                     #type: ignore
                        'menuitem_id': cart_item.menuitem.id,  #type: ignore
                        'quantity': cart_item.quantity,
                        'unit_price': cart_item.unit_price,
                        'price': cart_item.price
                    }
                )
                serialized_orderitems.is_valid(raise_exception=True)
                serialized_orderitems.save()
                serialized_items.append(serialized_orderitems.data)

            cart_items.delete()
            
            response_data = {
                'order': serialized_order.data,
                'order_items': serialized_items
            }
            return Response(response_data, status.HTTP_201_CREATED)
        else:
            return Response(status.HTTP_404_NOT_FOUND)
        
@api_view(['GET','PUT','PATCH','DELETE'])
@permission_classes([IsAuthenticated]) 
@throttle_classes([UserRateThrottle])     
def single_order(request, id):
    if request.method == 'GET':
        order = get_object_or_404(Order, pk=id)
        if order.user == request.user:
            order_items = OrderItem.objects.filter(order=id)
            serialized_order_items = OrderItemSerializer(order_items, many=True)
            serialized_order = OrderSerializer(order)
            response_data = {
                'order': serialized_order.data,
                'order_items': serialized_order_items.data
            }
            return Response(response_data)
        else:
            return Response(status.HTTP_403_FORBIDDEN)
        
    elif (request.method == 'PUT' or request.method == 'PATCH'):
        if (request.user.groups.filter(name='Manager').exists()):
            order = get_object_or_404(Order, pk=id)

            serialized_order = OrderSerializer(order, data={
                'delivery_crew': request.data['delivery crew'],
                'status': request.data['status']
                },partial=True)
            serialized_order.is_valid(raise_exception=True)
            serialized_order.save()
            return Response(status.HTTP_201_CREATED)
            
        elif (request.user.groups.filter(name='Delivery Crew').exists()):
            order = get_object_or_404(Order, pk=id)
            serialized_order = OrderSerializer(order, data={'status': request.data['status']}, partial=True)
            serialized_order.is_valid(raise_exception=True)
            serialized_order.save()
            return Response(status.HTTP_201_CREATED)
        else:
            return Response(status.HTTP_401_UNAUTHORIZED)
            
    elif request.method == 'DELETE':
        if (request.user.groups.filter(name='Manager').exists()):
            order = get_object_or_404(Order, pk=id)
            order.delete()
            return Response(status.HTTP_200_OK)
        else:
            return Response(status.HTTP_401_UNAUTHORIZED)
        
        
@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def user_managers(request):
    if request.method == 'GET':
        if (request.user.groups.filter(name='Manager').exists()):
            group = get_object_or_404(Group, name='Manager')
            managers = group.user_set.all()                                                                                     #type: ignore
            manager_list = [str(manager) for manager in managers]
            return Response(manager_list)
        else:
            return Response(status.HTTP_401_UNAUTHORIZED)
    elif request.method == 'POST':
        if (request.user.groups.filter(name='Manager').exists()):

            username = request.data['username']
            if username:
                user = get_object_or_404(User, username=username)

                managers = Group.objects.get(name="Manager")
                if user.groups.filter(name='manager').exists():
                    return Response({'error message': 'User is already in the manager group'}, status.HTTP_400_BAD_REQUEST)
                managers.user_set.add(user)                                                                                     #type: ignore
                return Response(status.HTTP_201_CREATED)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(status.HTTP_401_UNAUTHORIZED)
    
    
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def del_from_manager(request, id):
    if (request.user.groups.filter(name='Manager').exists()):
        user = get_object_or_404(User, pk=id)
        managers = Group.objects.get(name="Manager")
        if not user.groups.filter(name='Manager').exists():
            return Response({'error': 'User is not in the manager group'}, status=status.HTTP_400_BAD_REQUEST)
        managers.user_set.remove(user)                                                                                              #type: ignore
        return Response(status.HTTP_200_OK)
    else:
        return Response(status.HTTP_401_UNAUTHORIZED)


@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def user_delivery_crew(request):
    if request.method == 'GET':
        if (request.user.groups.filter(name='Manager').exists()):
            group = get_object_or_404(Group, name='Delivery Crew')
            delivery_crew = group.user_set.all()     #type: ignore
            delivery_crew_list = [str(user_delivery_crew) for user_delivery_crew in delivery_crew]
            return Response(delivery_crew_list)
        else:
            return Response(status.HTTP_401_UNAUTHORIZED)

    elif request.method == 'POST':
        if (request.user.groups.filter(name='Manager').exists()):

            username = request.data['username']
            if username:
                user = get_object_or_404(User, username=username)

                delivery_crew = Group.objects.get(name="Delivery Crew")
                if user.groups.filter(name='Delivery Crew').exists():
                    return Response({'error message': 'User is already in the Delivery crew group'}, status.HTTP_400_BAD_REQUEST)
                delivery_crew.user_set.add(user)                                                                                     #type: ignore
                return Response(status.HTTP_201_CREATED)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(status.HTTP_401_UNAUTHORIZED)
        
    
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def del_from_delivery_crew(request, id):
    if (request.user.groups.filter(name='Manager').exists()):
        user = get_object_or_404(User, pk=id)
        delivery_crew = Group.objects.get(name="Delivery Crew")
        if not user.groups.filter(name='Delivery Crew').exists():
            return Response({'error': 'User is not in the Delivery Crew group'}, status=status.HTTP_400_BAD_REQUEST)
        delivery_crew.user_set.remove(user)                                                                                          #type: ignore
        return Response(status.HTTP_200_OK)
    else:
        return Response(status.HTTP_401_UNAUTHORIZED)