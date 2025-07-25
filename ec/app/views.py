from django.shortcuts import render , redirect
from django.views import View

from .forms import CustomerProfileForm, CustomerRegistrationFrom
from django.contrib import messages
from . models import Customer, Product
from django.db.models import Count

# Create your views here.
def home(request):
    return render(request,"app/home.html")

def about(request):
    return render(request,"app/about.html")

def contact(request):
    return render(request,"app/contact.html")

class categoryView(View):
    def get(self,request,val):
        product = Product.objects.filter(category=val)
        title= Product.objects.filter(category=val).values('title')
        return render(request,"app/category.html",locals())
    

class categoryTitle(View):
    def get(self,request,val):
        product = Product.objects.filter(title=val)
        title= Product.objects.filter(category=product[0].category).values('title')
        return render(request,"app/category.html",locals())
    
class ProductDetail(View):
    def get (self,request,pk):
        product=Product.objects.get(pk=pk)
        return render(request,"app/productdetail.html",locals())
    
class CustomerRegistrationView(View):
    def get(self,request):
        form = CustomerRegistrationFrom()
        return render(request, 'app/customerregistration.html',locals() )
    def post(self, request):
        form = CustomerRegistrationFrom(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,"congratulations! User Register Successfully")
        else:
            messages.warning(request," Invalid Input Data ")
        return render(request, 'app/customerregistration.html',locals())

class ProfileView(View):
    def get(self,request):
        form = CustomerProfileForm()
        return render (request , 'app/profile.html', locals())
    
    def post(self , request):
        form=CustomerProfileForm(request.POST)
        if form.is_valid():
            user = request.user
            name= form.cleaned_data['name']
            locality = form.cleaned_data['locality']
            city = form.cleaned_data['city']
            mobile = form.cleaned_data['mobile']
            zipcode = form.cleaned_data['zipcode']
            state =  form.cleaned_data['state']

            reg = Customer(user=user,name=name,locality=locality,city=city,mobile=mobile, zipcode=zipcode,state=state)
            reg.save()
            messages.success(request,"Congratulation! Profile Save Successfully")
        else:
            messages.warning(request,"Invalid Input Data")
    

        return render (request , 'app/profile.html', locals())
    
def address(request):
    add =  Customer.objects.filter(user=request.user)
    return render(request, 'app/address.html', locals())

class updateAddress(View):
    def get(self, request,pk):
        add=Customer.objects.get(pk=pk)
        form=CustomerProfileForm(instance=add)
        return render(request,'app/updateAddress.html',locals())
    def post(self, request ,pk ):
        form=CustomerProfileForm(request.POST)
        if form.is_valid():
            add=Customer.objects.get(pk=pk)
            add.name = form.cleaned_data['name']
            add. locality = form.cleaned_data['locality']
            add.city = form.cleaned_data['city']
            add.mobile = form.cleaned_data['mobile']
            add.zipcode = form.cleaned_data['zipcode']
            add.state =  form.cleaned_data['state']
            add.save()

            messages.success(request," Congratulations! Profile Update Successfully")
        else:
            messages.warning(request, "Invalid Input Data")


        return redirect("address")
        