from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/post/<slug:slug>/', views.blog_detail, name='blog_detail'),
    path('blog/post/<slug:slug>/comment/', views.add_comment, name='add_comment'),
    path('blog/post/<slug:slug>/like/', views.toggle_like, name='toggle_like'),
    path('blog/post/<slug:slug>/dislike/', views.toggle_dislike, name='toggle_dislike'),
    path('blog/post/<slug:slug>/bookmark/', views.toggle_bookmark, name='toggle_bookmark'),
    path('author/<slug:slug>/', views.author_detail, name='author_detail'),
    path('bloggers/', views.blogger_list, name='blogger_list'),
    path('search/', views.search, name='search'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup, name='signup'),
    path('profile/', views.profile, name='profile'),
    path('favorites/', views.favorites, name='favorites'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
] 