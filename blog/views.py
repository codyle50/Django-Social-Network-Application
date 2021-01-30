from django.core.checks import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Comment, Post
from .forms import CommentForm
from django.http import HttpResponseRedirect, JsonResponse
from users.models import Profile
from itertools import chain
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.template.loader import render_to_string


def home(request):
    context = {
        'posts':Post.objects.all()
    }
    return render(request, 'blog/home.html', context)

@login_required
def posts_of_following_profiles(request):

    profile = Profile.objects.get(user = request.user)
    users = [user for user in profile.following.all()]
    posts = []
    qs = None
    for u in users:
        p = Profile.objects.get(user=u)
        p_posts = p.user.post_set.all()
        posts.append(p_posts)
    my_posts = profile.profile_posts()
    posts.append(my_posts)
    if len(posts)>0:
        qs = sorted(chain(*posts), reverse=True, key=lambda obj:obj.date_posted)
  
    return render(request,'blog/feeds.html',{'profile':profile,'posts':qs})


@login_required
def LikeView(request):
    # post = get_object_or_404(Post, id=request.POST.get('post_id'))
    post = get_object_or_404(Post, id=request.POST.get('id'))
    liked = False
    if post.likes.filter(id=request.user.id).exists():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True

    context = {
        'post':post,
        'total_likes':post.total_likes(),
        'liked':liked,
    }

    if request.is_ajax():
        html = render_to_string('blog/like_section.html',context, request=request)
        return JsonResponse({'form':html})
    # return HttpResponseRedirect(post.get_absolute_url())

@login_required
def SaveView(request):
    # post = get_object_or_404(Post, id=request.POST.get('post_sid'))
    post = get_object_or_404(Post, id=request.POST.get('id'))
    saved = False
    if post.saves.filter(id=request.user.id).exists():
        post.saves.remove(request.user)
        saved = False
    else:
        post.saves.add(request.user)
        saved = True
    
    context = {
        'post':post,
        'total_saves':post.total_saves(),
        'saved':saved,
    }

    if request.is_ajax():
        html = render_to_string('blog/save_section.html',context, request=request)
        return JsonResponse({'form':html})
    # return HttpResponseRedirect(reverse('post-detail', args=[str(pk)]))


@login_required
def LikeCommentView(request, id1, id2):
    post = get_object_or_404(Comment, id=request.POST.get('comment_id'))
    cliked = False
    if post.likes.filter(id=request.user.id).exists():
        post.likes.remove(request.user)
        cliked = False
    else:
        post.likes.add(request.user)
        cliked = True
    return HttpResponseRedirect(reverse('post-detail', args=[str(id1)]))


class PostListView(ListView):
    model = Post
    template_name = 'blog/home.html' # <app>/<model>_<viewtype>.html
    context_object_name = 'posts'
    ordering = ['-date_posted']
    paginate_by = 5


class UserPostListView(ListView):
    model = Post
    template_name = 'blog/user_posts.html' # <app>/<model>_<viewtype>.html
    context_object_name = 'posts'
    paginate_by = 5

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        return Post.objects.filter(author=user).order_by('-date_posted')


# class PostDetailView(DetailView):
#     model = Post

#     def get_context_data(self, *args,**kwargs):
#         context = super(PostDetailView, self).get_context_data()
#         stuff = get_object_or_404(Post, id=self.kwargs['pk'])
#         total_likes = stuff.total_likes()
#         total_saves = stuff.total_saves()
#         total_comments = stuff.comments.all()

#         tcl={}
#         for cmt in total_comments:
#             total_clikes = cmt.total_clikes()
#             cliked = False
#             if cmt.likes.filter(id=self.request.user.id).exists():
#                 cliked = True

#             tcl[cmt.id] = cliked
#         context["clikes"]=tcl


#         liked = False
#         if stuff.likes.filter(id=self.request.user.id).exists():
#             liked = True
#         context["total_likes"]=total_likes
#         context["liked"]=liked


#         saved = False
#         if stuff.saves.filter(id=self.request.user.id).exists():
#             saved = True
#         context["total_saves"]=total_saves
#         context["saved"]=saved

#         return context
    

#     def render_to_response(self, context, **response_kwargs):
#         if self.request.is_ajax():
#             html = render_to_string('blog/like_section.html',context, request=self.request)
#             return JsonResponse({'form':html})
#             # return JsonResponse('Success',safe=False, **response_kwargs)
#         else:
#             return super(PostDetailView,self).render_to_response(context, **response_kwargs)


def PostDetailView(request,pk):

    stuff = get_object_or_404(Post, id=pk)
    total_likes = stuff.total_likes()
    total_saves = stuff.total_saves()
    # total_comments = Comment.objects.filter(post=stuff, reply=None).order_by('-id')
    total_comments = stuff.comments.all().filter(reply=None).order_by('-id')
    total_comments2 = stuff.comments.all().order_by('-id')

    context = {}


    if request.method == "POST":
        comment_qs = None
        comment_form = CommentForm(request.POST or None)
        if comment_form.is_valid():
            form = request.POST.get('body')
            reply_id = request.POST.get('comment_id')
            if reply_id:
                comment_qs = Comment.objects.get(id=reply_id)
            
            comment = Comment.objects.create(name=request.user,post=stuff,body=form, reply=comment_qs)
            comment.save() 
            total_comments = stuff.comments.all().filter(reply=None).order_by('-id')
            total_comments2 = stuff.comments.all().order_by('-id')
    else:
        comment_form = CommentForm()
             

    tcl={}
    for cmt in total_comments2:
        total_clikes = cmt.total_clikes()
        cliked = False
        if cmt.likes.filter(id=request.user.id).exists():
            cliked = True

        tcl[cmt.id] = cliked
    context["clikes"]=tcl


    liked = False
    if stuff.likes.filter(id=request.user.id).exists():
        liked = True
    context["total_likes"]=total_likes
    context["liked"]=liked


    saved = False
    if stuff.saves.filter(id=request.user.id).exists():
        saved = True
    context["total_saves"]=total_saves
    context["saved"]=saved
    
    
    

    context['comment_form'] = comment_form

    context['post']=stuff
    context['comments']=total_comments

    if request.is_ajax():
        html = render_to_string('blog/comments.html',context, request=request)
        return JsonResponse({'form':html})

    return render(request, 'blog/post_detail.html', context)


# <fieldset class="form-group">
#     <legend class=" mb-4">Add Comment</legend>
#     <textarea style="width: 100%;" name="body" id="cmtbody" cols="40" rows="5"></textarea>
# </fieldset>
# <div class="form-group">
#     <button class="btn btn-outline-info" type="submit">Add Comment</button>
# </div>


# {% csrf_token %}
# <input type="hidden" name="comment_id" value="{{comment.id}}">
# <fieldset class="form-group">
#     <legend class="h5 mb-4">Replies :</legend>
#     <textarea style="width: 100%;" name="body" id="cmt-body" cols="40" rows="2"></textarea>
# </fieldset>
# <div class="form-group">
#     <button class="btn btn-outline-info" type="submit">Reply</button>
# </div>

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    fields =['title', 'content']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


# @login_required
# def add_comment(request, pk):
#     form = request.POST.get('body')
#     reply_id = request.POST.get('comment_id')
#     comment_qs = None
#     if reply_id:
#         comment_qs = Comment.objects.get(id=reply_id)
#     if request.method == "POST" and form:
#         user = request.user
#         post = get_object_or_404(Post, pk=pk)
        
#         comment = Comment(name=user,post=post,body=form, reply=comment_qs)
#         comment.save() 
        # return redirect('post-detail', post.id)
    # return redirect('post-detail', pk)





class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    fields =['title', 'content']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False

class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    success_url = '/'

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False

def about(request):
    return render(request, 'blog/about.html', {'title':'About'})

def search(request):
    query = request.GET['query']
    if len(query) >= 150 or len(query) < 1:
        allposts = Post.objects.none()
    else:
        allpostsTitle = Post.objects.filter(title__icontains=query)
        allpostsAuthor = Post.objects.filter(author__username = query)
        allposts = allpostsAuthor.union(allpostsTitle)
    
    params = {'allposts': allposts}
    return render(request, 'blog/search_results.html', params)


@login_required
def AllLikeView(request):
    user = request.user
    liked_posts = user.blogpost.all()
    context = {
        'liked_posts':liked_posts
    }
    return render(request, 'blog/liked_posts.html', context)

@login_required
def AllSaveView(request):
    user = request.user
    saved_posts = user.blogsave.all()
    context = {
        'saved_posts':saved_posts
    }
    return render(request, 'blog/saved_posts.html', context)
