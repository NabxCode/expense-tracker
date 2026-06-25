from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.dashboard, name='dashboard'),
    path('expenses/add/', views.add_expense, name='add_expense'),
    path('expenses/<int:pk>/edit/', views.edit_expense, name='edit_expense'),
    path('expenses/<int:pk>/delete/', views.delete_expense, name='delete_expense'),
    path('budget/set/', views.set_budget, name='set_budget'),
    path('chart-data/', views.chart_data, name='chart_data'),
    path('categories/', views.manage_categories, name='manage_categories'),
path('categories/<int:pk>/delete/', views.delete_category, name='delete_category'),
]
