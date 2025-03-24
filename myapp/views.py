from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm, UserChangeForm
from django.urls import reverse
from django.http import JsonResponse
from django.db.models import Q
from .models import BlogPost, Author, Comment, Like, Bookmark, Profile, Favorite
from .forms import CustomUserCreationForm, CommentForm

def get_base_context():
    return {
        'authors': Author.objects.all(),
    }

def home(request):
    posts = BlogPost.objects.all().order_by('-created_at')[:5]
    categories = BlogPost.objects.values_list('category', flat=True).distinct()
    authors = Author.objects.all()
    
    context = {
        'posts': posts,
        'categories': categories,
        'authors': authors,
    }
    return render(request, 'index.html', context)

def blog_list(request):
    category = request.GET.get('category')
    if category:
        posts = BlogPost.objects.filter(category=category)
    else:
        posts = BlogPost.objects.all()
    
    posts = posts.order_by('-created_at')
    categories = BlogPost.objects.values_list('category', flat=True).distinct()
    authors = Author.objects.all()
    
    context = {
        'posts': posts,
        'categories': categories,
        'authors': authors,
    }
    return render(request, 'blog_list.html', context)

def author_detail(request, slug):
    author = get_object_or_404(Author, slug=slug)
    author_posts = BlogPost.objects.filter(author=author).order_by('-created_at')
    categories = BlogPost.objects.values_list('category', flat=True).distinct()
    authors = Author.objects.all()
    
    context = {
        'author': author,
        'author_posts': author_posts,
        'categories': categories,
        'authors': authors,
    }
    
    return render(request, 'author_detail.html', context)

def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    comments = post.comments.all()
    categories = BlogPost.objects.values_list('category', flat=True).distinct()
    authors = Author.objects.all()
    
    # Get user's like/dislike status
    user_like = None
    is_favorite = False
    if request.user.is_authenticated:
        user_like = Like.objects.filter(user=request.user, post=post).first()
        is_favorite = Favorite.objects.filter(user=request.user, post=post).exists()
    
    # Get counts
    likes_count = post.like_count
    dislikes_count = post.dislike_count
    
    context = {
        'post': post,
        'comments': comments,
        'categories': categories,
        'authors': authors,
        'user_like': user_like,
        'is_favorite': is_favorite,
        'likes_count': likes_count,
        'dislikes_count': dislikes_count,
    }
    return render(request, 'blog_detail.html', context)

@login_required
def create_comment(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            messages.success(request, 'Your comment has been added successfully!')
            return redirect('blog_detail', slug=slug)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CommentForm()
    
    context = {
        'form': form,
        'post': post,
        **get_base_context()
    }
    return render(request, 'create_comment.html', context)

def blogger_list(request):
    authors = Author.objects.all()
    categories = BlogPost.objects.values_list('category', flat=True).distinct()
    context = {
        'authors': authors,
        'categories': categories,
    }
    return render(request, 'blogger_list.html', context)

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create a profile for the new user
            Profile.objects.create(user=user)
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    
    categories = BlogPost.objects.values_list('category', flat=True).distinct()
    authors = Author.objects.all()
    context = {
        'form': form,
        'categories': categories,
        'authors': authors,
    }
    return render(request, 'signup.html', context)

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                next_url = request.GET.get('next')
                return redirect(next_url if next_url else 'home')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    context = {
        'form': form,
        **get_base_context()
    }
    return render(request, 'login.html', context)

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')

@login_required
def toggle_like(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    like, created = Like.objects.get_or_create(
        post=post,
        user=request.user,
        defaults={'is_like': True}
    )
    
    if not created:
        if like.is_like:
            like.delete()
        else:
            like.is_like = True
            like.save()
    
    return JsonResponse({
        'like_count': post.like_count,
        'dislike_count': post.dislike_count,
        'is_liked': True if created or like.is_like else False
    })

@login_required
def toggle_dislike(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    like, created = Like.objects.get_or_create(
        post=post,
        user=request.user,
        defaults={'is_like': False}
    )
    
    if not created:
        if not like.is_like:
            like.delete()
        else:
            like.is_like = False
            like.save()
    
    return JsonResponse({
        'like_count': post.like_count,
        'dislike_count': post.dislike_count,
        'is_disliked': True if created or not like.is_like else False
    })

@login_required
def toggle_bookmark(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    bookmark, created = Bookmark.objects.get_or_create(user=request.user, post=post)
    
    if not created:
        bookmark.delete()
        is_bookmarked = False
    else:
        is_bookmarked = True
    
    return JsonResponse({
        'is_bookmarked': is_bookmarked,
        'bookmark_count': post.bookmark_set.count()
    })

def search(request):
    query = request.GET.get('q', '')
    if query:
        posts = BlogPost.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(category__icontains=query)
        ).order_by('-created_at')
    else:
        posts = []
    
    categories = BlogPost.objects.values_list('category', flat=True).distinct()
    authors = Author.objects.all()
    
    context = {
        'posts': posts,
        'query': query,
        'categories': categories,
        'authors': authors,
    }
    return render(request, 'search_results.html', context)

def about(request):
    context = {
        'authors': Author.objects.all(),
    }
    return render(request, 'about.html', context)

def contact(request):
    if request.method == 'POST':
        # Here you would typically handle the form submission
        # For now, we'll just show a success message
        messages.success(request, 'Thank you for your message! We will get back to you soon.')
        return redirect('contact')
    
    context = {
        'authors': Author.objects.all(),
    }
    return render(request, 'contact.html', context)

@login_required
def add_comment(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Comment.objects.create(
                post=post,
                author=request.user,
                content=content
            )
            messages.success(request, 'Your comment has been added successfully!')
        else:
            messages.error(request, 'Please provide a comment.')
    return redirect('blog_detail', slug=slug)

@login_required
def profile(request):
    if request.method == 'POST':
        # Update user information
        request.user.first_name = request.POST.get('first_name')
        request.user.last_name = request.POST.get('last_name')
        request.user.email = request.POST.get('email')
        request.user.save()
        
        # Update profile information
        profile, created = Profile.objects.get_or_create(user=request.user)
        profile.bio = request.POST.get('bio')
        profile.location = request.POST.get('location')
        profile.website = request.POST.get('website')
        profile.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    # Get or create profile
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    context = {
        'profile': profile,
        'categories': BlogPost.objects.values_list('category', flat=True).distinct(),
        'authors': Author.objects.all(),
    }
    return render(request, 'profile.html', context)

@login_required
def favorites(request):
    favorite_posts = BlogPost.objects.filter(favorite__user=request.user).order_by('-favorite__created_at')
    context = {
        'favorite_posts': favorite_posts,
        'categories': BlogPost.objects.values_list('category', flat=True).distinct(),
        'authors': Author.objects.all(),
    }
    return render(request, 'favorites.html', context)

@login_required
def like_post(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    
    if not created:
        if like.is_like:
            like.delete()
        else:
            like.is_like = True
            like.save()
    else:
        like.is_like = True
        like.save()
    
    return redirect('blog_detail', slug=slug)

@login_required
def dislike_post(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    
    if not created:
        if not like.is_like:
            like.delete()
        else:
            like.is_like = False
            like.save()
    else:
        like.is_like = False
        like.save()
    
    return redirect('blog_detail', slug=slug)

@login_required
def toggle_favorite(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    favorite, created = Favorite.objects.get_or_create(user=request.user, post=post)
    
    if not created:
        favorite.delete()
        messages.success(request, 'Post removed from favorites.')
    else:
        messages.success(request, 'Post added to favorites.')
    
    return redirect('blog_detail', slug=slug) 