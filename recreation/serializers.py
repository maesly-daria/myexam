from rest_framework import serializers

from .models import Booking, House, Review


class HouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = House
        fields = ["house_id", "name", "location", "capacity", "price_per_night"]


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = [
            "booking_id",
            "house",
            "check_in_date",
            "check_out_date",
            "total_cost",
        ]


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["review_id", "house_id", "client_id", "rating", "comment"]
