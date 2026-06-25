from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from .forms import RegisterForm, ExpenseForm
from .models import Expense, Category
from django.http import JsonResponse
import json


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    expenses = Expense.objects.filter(user=request.user)

    category_filter = request.GET.get('category')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if category_filter:
        expenses = expenses.filter(category__id=category_filter)
    if date_from:
        expenses = expenses.filter(date__gte=date_from)
    if date_to:
        expenses = expenses.filter(date__lte=date_to)

    total = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    categories = Category.objects.filter(user=request.user)

    # Budget alert logic
    from datetime import date
    from .models import Budget
    today = date.today()
    budget = Budget.objects.filter(
        user=request.user, month__year=today.year, month__month=today.month).first()
    budget_alert = None
    if budget:
        monthly_total = Expense.objects.filter(
            user=request.user,
            date__year=today.year,
            date__month=today.month
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        percentage = (monthly_total / budget.limit) * 100
        if percentage >= 90:
            budget_alert = f"Warning: You have used {percentage:.1f}% of your monthly budget (₹{monthly_total} of ₹{budget.limit})"

    return render(request, 'dashboard.html', {
        'expenses': expenses,
        'total': total,
        'categories': categories,
        'budget_alert': budget_alert,
        'budget': budget,
    })


@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST, user=request.user)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            return redirect('dashboard')
    else:
        form = ExpenseForm(user=request.user)
    return render(request, 'expenses/add.html', {'form': form})


@login_required
def edit_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = ExpenseForm(instance=expense, user=request.user)
    return render(request, 'expenses/edit.html', {'form': form})


@login_required
def delete_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    if request.method == 'POST':
        expense.delete()
        return redirect('dashboard')
    return render(request, 'expenses/confirm_delete.html', {'expense': expense})


@login_required
def set_budget(request):
    from datetime import date
    from .models import Budget
    today = date.today()
    budget = Budget.objects.filter(
        user=request.user, month__year=today.year, month__month=today.month).first()
    if request.method == 'POST':
        limit = request.POST.get('limit')
        if budget:
            budget.limit = limit
            budget.save()
        else:
            Budget.objects.create(user=request.user, month=today, limit=limit)
        return redirect('dashboard')
    return render(request, 'set_budget.html', {'budget': budget})


@login_required
def chart_data(request):
    from datetime import date
    from django.db.models import Sum

    # Pie chart data — expenses by category
    category_data = Expense.objects.filter(user=request.user).values(
        'category__name'
    ).annotate(total=Sum('amount'))

    pie_labels = []
    pie_values = []
    for item in category_data:
        label = item['category__name'] if item['category__name'] else 'Uncategorized'
        pie_labels.append(label)
        pie_values.append(float(item['total']))

    # Bar chart data — last 6 months spending
    today = date.today()
    bar_labels = []
    bar_values = []
    for i in range(5, -1, -1):
        month = (today.month - i - 1) % 12 + 1
        year = today.year if today.month - i > 0 else today.year - 1
        total = Expense.objects.filter(
            user=request.user,
            date__year=year,
            date__month=month
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        bar_labels.append(f"{year}-{month:02d}")
        bar_values.append(float(total))

    return JsonResponse({
        'pie_labels': pie_labels,
        'pie_values': pie_values,
        'bar_labels': bar_labels,
        'bar_values': bar_values,
    })


@login_required
def manage_categories(request):
    from .models import Category
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            Category.objects.create(user=request.user, name=name)
        return redirect('manage_categories')
    categories = Category.objects.filter(user=request.user)
    return render(request, 'manage_categories.html', {'categories': categories})


@login_required
def delete_category(request, pk):
    from .models import Category
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        category.delete()
        return redirect('manage_categories')
    return redirect('manage_categories')
