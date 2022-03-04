import datetime
from distutils.command.install_data import install_data

from django.core.checks import messages
from django.http import HttpResponseRedirect, JsonResponse

from django.shortcuts import render
from django.urls import reverse_lazy, reverse
from django.views.generic import *
from django.contrib.messages import *
from .forms import *


def home(request):
    return render(request, "inventory/home.html")


def product(request):
    producto = ProductoForm()
    context = {
        'form': producto,
        'msg': '',
        'texto': ''
    }
    if request.method == 'POST':
        producto_form = ProductoForm(request.POST)
        if producto_form.is_valid():
            nombre = producto_form.cleaned_data['nombre']
            cantidad = producto_form.cleaned_data['cantidad']
            fecha_entrada = producto_form.cleaned_data['fecha_entrada'].split("-")
            precio_costo = producto_form.cleaned_data['precio_costo']
            precio_venta = producto_form.cleaned_data['precio_venta']
            es_central = producto_form.cleaned_data['almacen_central']
            anho = int(fecha_entrada[0])
            mes = int(fecha_entrada[1])
            dia = int(fecha_entrada[2])
            producto = Producto(nombre=nombre,
                                cantidad=cantidad,
                                fecha_entrada=datetime.datetime(anho, mes, dia),
                                precio_costo=precio_costo,
                                precio_venta=precio_venta
                                )
            try:
                producto.save()
                if Existencia.objects.all().filter(producto=producto.id,
                                                   almacen=Almacen.objects.get(nombre=es_central).id).count() == 0:
                    e = Existencia(almacen=Almacen.objects.get(nombre=es_central), producto=producto,
                                   cantidad=cantidad)
                    try:
                        e.save()
                    except:
                        pass
            except:
                return render(request, 'inventory/producto/create_product.html', context)
            else:
                return HttpResponseRedirect(reverse('inv:list_product'))
        else:
            context['msg'] = 'true'
            context['texto'] = 'almacen_error'
            return render(request, 'inventory/producto/create_product.html', context)
    else:
        return render(request, 'inventory/producto/create_product.html', context)


class ProductoDeleteView(DeleteView):
    model = Producto
    template_name = 'inventory/producto/delete_product.html'
    success_url = 'inv:list_product'


class ProductoListView(ListView):
    model = Producto
    context_object_name = 'object'
    ordering = ['nombre']
    template_name = 'inventory/producto/list_product.html'


def update_producto(request, pk):
    object = Producto.objects.get(id=int(pk))
    form = ProductoForm(instance=object)
    context = {
        'form': form,
        'msg': 'update'
    }
    return render(request, 'inventory/producto/create_product.html', context)


def create_almacen(request):
    almacen = AlmacenForm()
    context = {
        'form': almacen,
    }
    if request.method == "POST":
        almacen_form = AlmacenForm(request.POST)
        if almacen_form.is_valid():
            nombre = almacen_form.cleaned_data['nombre']
            es_central = almacen_form.cleaned_data['es_central']
            almacen = Almacen(nombre=nombre, es_central=es_central)
            try:
                almacen.save()
                return HttpResponseRedirect(reverse('inv:list_almacen'))
            except:
                return render(request, 'inventory/almacen/create_almacen.html', context)
        else:
            return render(request, 'inventory/almacen/create_almacen.html', context)
    else:
        return render(request, 'inventory/almacen/create_almacen.html', context)


class AlmacenDeleteView(DeleteView):
    model = Almacen
    template_name = 'inventory/almacen/delete_almacen.html'
    success_url = reverse_lazy('inv:list_almacen')


class AlmacenListView(ListView):
    model = Almacen
    context_object_name = 'object'
    ordering = ['nombre']
    template_name = 'inventory/almacen/list_almacen.html'


def productos_almacen(request, pk):
    res = dict()
    existencia = Existencia.objects.all()
    for e in existencia:
        if e.almacen.id == int(pk):
            res[e.producto.nombre] = e.cantidad
    return render(request, 'inventory/productos_almacen.html', {'content': res,
                                                                'almacen': Almacen.objects.get(id=int(pk)).nombre})


def movimiento(request):
    mov = MovimientoForm()
    context = {
        'form': mov,
        'mess': ''
    }
    if request.method == "POST":
        mov_form = MovimientoForm(request.POST)
        if mov_form.is_valid():
            origen = mov_form.cleaned_data['almacen_origen']
            destino = mov_form.cleaned_data['almacen_destino']
            producto = mov_form.cleaned_data['producto']
            cantidad = mov_form.cleaned_data['cantidad']
            if origen == destino:
                context['mess'] = 'doubled'
                return render(request, 'inventory/movimiento.html', context)
            else:
                if Existencia.objects.get(almacen=origen.id, producto=producto.id).cantidad > int(cantidad):
                    mov_instance = Movimiento(almacen_origen=origen, almacen_destino=destino,
                                              producto=producto, cantidad=int(cantidad))
                    e = Existencia.objects.get(almacen=origen.id, producto=producto.id)
                    e.cantidad -= int(cantidad)
                    e.save()
                    e = Existencia.objects.get(almacen=destino.id, producto=producto.id).cantidad
                    e.cantidad += int(cantidad)
                    e.save()
                    try:
                        mov_instance.save()
                        return HttpResponseRedirect(reverse('inv:list_almacen'))
                    except:
                        return render(request, 'inventory/movimiento.html', context)
                elif Existencia.objects.get(almacen=origen.id, producto=producto.id).cantidad == int(cantidad):
                    Existencia.objects.get(almacen=origen.id, producto=producto.id).delete()
                    e = Existencia.objects.get(almacen=destino.id, producto=producto.id).cantidad
                    e.cantidad += int(cantidad)
                    e.save()
                    return render(request, 'inventory/almacen/create_almacen.html', context)
                elif Existencia.objects.filter(almacen=destino.id, producto=producto.id).count() == 0:
                    e = Existencia.objects.get(almacen=origen.id, producto=producto.id)
                    e.cantidad -= int(cantidad)
                    e.save()
                    e = Existencia(almacen=origen.id, producto=producto.id, cantidad=cantidad)
                    e.save()
                else:
                    context['mess'] = 'err'
                    return render(request, 'inventory/movimiento.html', context)
        else:
            return render(request, 'inventory/almacen/create_almacen.html', context)
    else:
        print("GET")
        return render(request, "inventory/movimiento.html", context)
