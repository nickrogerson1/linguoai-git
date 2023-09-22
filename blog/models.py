from django import forms
from django.db import models

from modelcluster.fields import ParentalKey, ParentalManyToManyField
from wagtail.models import Page, Orderable
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.search import index
from wagtail.snippets.models import register_snippet
from wagtail.images.models import Image, AbstractImage, AbstractRendition
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator


from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase
import datetime



# Use this to add as a reference when adding pagination
# https://learnwagtail.com/tutorials/how-to-paginate-your-wagtail-pages/

class HomePage(Page):
    body = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('body'),
    ]



class CustomImage(AbstractImage):

    alt_text = models.CharField(max_length=255, blank=True)
    admin_form_fields = Image.admin_form_fields + ('alt_text',)


class CustomRendition(AbstractRendition):
    image = models.ForeignKey(CustomImage, on_delete=models.CASCADE, related_name='renditions')

    class Meta:
        unique_together = (
            ('image', 'filter_spec', 'focal_point_key'),
        )


class BlogPageTag(TaggedItemBase):
    content_object = ParentalKey(
        'BlogPage',
        related_name='tagged_items',
        on_delete=models.CASCADE
    )

class BlogPage(Page):
    date = models.DateField("Post date")
    intro = models.CharField(max_length=250)
    body = RichTextField(blank=True)
    authors = ParentalManyToManyField('blog.Author', blank=True)

    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)
    categories = ParentalManyToManyField("blog.BlogCategory", blank=True)

    main_image = models.ForeignKey(
        CustomImage, null=True, on_delete=models.SET_NULL, related_name='+'
    )

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('date'),
            FieldPanel('authors', widget=forms.CheckboxSelectMultiple),
            FieldPanel('tags'),
            FieldPanel("categories", widget=forms.CheckboxSelectMultiple)
        ], 
        heading="Blog information"),
        FieldPanel('main_image'),
        FieldPanel('intro'),
        FieldPanel('body'),
        InlinePanel('gallery_images', label="Gallery images"),
    ]

    def get_context(self, request):
        context = super().get_context(request)
        context['year'] = datetime.date.today().year
        return context


class PaginatorMixin:

    def return_with_pagination(self, request, context, blogpages, snippet_type=None, keyword_name=None, slug=None):

        paginator = Paginator(blogpages, 18)
        page = request.GET.get("page")

        try:
            posts = paginator.page(page)
        except PageNotAnInteger:
            posts = paginator.page(1)
        except EmptyPage:
            posts = paginator.page(paginator.num_pages)

        if snippet_type == 'tag':
            context['tag'] = keyword_name
        elif snippet_type == 'cat':
            context['cat'] = keyword_name
            context['cat_slug'] = slug
        elif snippet_type == 'author':
            context['author'] = keyword_name

        context['blogpages'] = posts
        context['year'] = datetime.date.today().year
        return context
    


class BlogIndexPage(Page, PaginatorMixin):
    intro = RichTextField(blank=True)
    # bp = BlogPage()

    content_panels = Page.content_panels + [
        FieldPanel('intro')
    ]

    def get_context(self, request):
    # Update context to include only published posts, ordered by reverse-chron
        context = super().get_context(request)
        blogpages = BlogPage.objects.live().order_by('-first_published_at')
        
        return self.return_with_pagination(request, context, blogpages)
    
    




class BlogTagIndexPage(Page, PaginatorMixin):
    template_name = 'blog/blog_index_page.html'

    def get_context(self, request):
        # Filter by tag
        context = super().get_context(request)

        tag = request.GET.get('tag')
        blogpages = BlogPage.objects.filter(tags__name=tag).order_by('-first_published_at')
        
        return self.return_with_pagination(request, context, blogpages, 'tag', tag)
    
    def get_template(self, request):
        return self.template_name
    


class BlogCategoryIndexPage(Page, PaginatorMixin):
    template_name = 'blog/blog_index_page.html'

    def get_context(self, request):

        context = super().get_context(request)
        category_slug = request.GET.get('category')
        blogpages = BlogPage.objects.filter(categories__slug=category_slug).order_by('-first_published_at')

        category_name = category_slug   

    # Work out what the category name is based on the slug and without doing a 2nd look up
        if blogpages:
            for cat in blogpages[0].categories.all():
                if cat.slug == category_slug:
                    category_name = cat.name
                    break

        return self.return_with_pagination(request, context, blogpages, 'cat', category_name, category_slug)
    
    def get_template(self, request):
        return self.template_name
    

class BlogAuthorIndexPage(Page, PaginatorMixin):
    template_name = 'blog/blog_index_page.html'

    def get_context(self, request):
        
        context = super().get_context(request)
        author = request.GET.get('author')
        blogpages = BlogPage.objects.filter(authors__name=author).order_by('-first_published_at')

        return self.return_with_pagination(request, context, blogpages, 'author', author)
    
    def get_template(self, request):
        return self.template_name





class BlogPageGalleryImage(Orderable):
    page = ParentalKey(BlogPage, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ForeignKey(
        'wagtailimages.Image', on_delete=models.CASCADE, related_name='+'
    )
    caption = models.CharField(blank=True, max_length=250)

    panels = [
        FieldPanel('image'),
        FieldPanel('caption'),
    ]



@register_snippet
class Author(models.Model):
    name = models.CharField(max_length=50)
    profile = models.TextField()
    author_image = models.ForeignKey(
        CustomImage, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )
    

    panels = [
        FieldPanel('name'),
        FieldPanel('profile'),
        FieldPanel('author_image'),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Authors'



@register_snippet
class BlogCategory(models.Model):
    """Blog category for a snippet."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(
        verbose_name="slug",
        allow_unicode=True,
        max_length=255,
        help_text='A slug to identify posts by this category',
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
    ]

    class Meta:
        verbose_name = "Blog Category"
        verbose_name_plural = "Blog Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name