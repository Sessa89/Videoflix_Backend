"""
Root URL configuration for Videoflix.

Routes:
- /admin/       → Django admin
- /django-rq/   → RQ dashboard (queue monitoring)
- /api/...      → Authentication & Video APIs (see app-level urls)

The app-level routers are included under the `/api/` prefix to present a
single, cohesive public API surface for the frontend.
"""


"""
URL configuration for videoflix_core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('django-rq/', include('django_rq.urls')),
    path('api/', include('authentication_app.api.urls')),
    path('api/', include('video_app.api.urls')),
]