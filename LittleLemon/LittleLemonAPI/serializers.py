from typing import Required
from wsgiref.validate import validator
from rest_framework import serializers 
from rest_framework.validators import UniqueTogetherValidator 
from django.contrib.auth.models import User 
from .models import MenuItem, Category, Cart, Order, OrderItem
 
 
class CategorySerializer (serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id','title']




class MenuItemSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(write_only=True)
    category = CategorySerializer(read_only=True)
    class Meta:
        model = MenuItem
        fields = ['id','title','price','featured','category','category_id']
        
        
        
class CartSerializer(serializers.ModelSerializer):  
    menuitem_id = serializers.IntegerField(write_only=True)
    menuitem = MenuItemSerializer(read_only=True)

    unit_price = serializers.DecimalField(max_digits=6, decimal_places=2, required = False)
    price = serializers.DecimalField(max_digits=6, decimal_places=2, required = False)
    
    class Meta:
        model = Cart
        fields = ['id','user','menuitem','menuitem_id','quantity','unit_price','price']
        validators = [
            UniqueTogetherValidator(
                queryset = Cart.objects.all(),
                fields = ['user','menuitem_id']
            )
        ]
    
    def create(self, validated_data):
        menuitem = MenuItem.objects.get(pk=validated_data['menuitem_id'])
        validated_data['unit_price'] = menuitem.price
        validated_data['price'] = menuitem.price * validated_data['quantity']
        
        return super().create(validated_data)
        


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id','user','delivery_crew','status','total','date']
     
     

class OrderItemSerializer(serializers.ModelSerializer):

    menuitem_id = serializers.IntegerField(write_only=True)
    menuitem = MenuItemSerializer(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id','order','menuitem','menuitem_id','quantity','unit_price','price']
        validators = [
            UniqueTogetherValidator(
                queryset = OrderItem.objects.all(),
                fields = ['menuitem_id','order']
            )
        ]        
        
