from django.urls import path, include
from .views import (
    TripListView, TripDetailView, StartTripView, EndTripView, TripTrackingView
)

urlpatterns = [
    path('', TripListView.as_view(), name='trip_list'),
    path('<int:pk>/', TripDetailView.as_view(), name='trip_detail'),
    path('start/', StartTripView.as_view(), name='start_trip'),
    path('<int:pk>/end/', EndTripView.as_view(), name='end_trip'),
    path('<int:pk>/track/', TripTrackingView.as_view(), name='track_trip'),
]