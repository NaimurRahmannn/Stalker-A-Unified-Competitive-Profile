from decimal import Decimal

from rest_framework import serializers

from apps.datathons.models import KaggleManualTrackStats, KaggleTrackStats


class KaggleManualTrackSerializer(serializers.ModelSerializer):
    rank_status = serializers.ChoiceField(choices=KaggleTrackStats.RankStatus.choices)
    global_rank = serializers.IntegerField(min_value=1, max_value=2**31 - 1, allow_null=True)
    highest_rank = serializers.IntegerField(min_value=1, max_value=2**31 - 1, allow_null=True)
    tier = serializers.ChoiceField(
        choices=("Novice", "Contributor", "Expert", "Master", "Grandmaster"), allow_null=True,
    )
    points = serializers.DecimalField(
        max_digits=14, decimal_places=4, min_value=Decimal("0"),
        max_value=Decimal("9999999999.9999"), allow_null=True,
    )
    gold_medals = serializers.IntegerField(min_value=0, max_value=2**31 - 1, allow_null=True)
    silver_medals = serializers.IntegerField(min_value=0, max_value=2**31 - 1, allow_null=True)
    bronze_medals = serializers.IntegerField(min_value=0, max_value=2**31 - 1, allow_null=True)

    class Meta:
        model = KaggleManualTrackStats
        fields = (
            "track", "rank_status", "global_rank", "highest_rank", "tier", "points",
            "gold_medals", "silver_medals", "bronze_medals", "updated_at",
        )
        read_only_fields = ("track", "updated_at")

    def validate(self, attrs):
        status = attrs["rank_status"]
        rank = attrs["global_rank"]
        if status == "ranked" and rank is None:
            raise serializers.ValidationError({"global_rank": "A ranked track needs a global rank."})
        if status != "ranked" and rank is not None:
            raise serializers.ValidationError({"global_rank": "Only ranked tracks may have a global rank."})
        if status == "unranked" and (attrs["tier"] is not None or attrs["points"] is not None):
            raise serializers.ValidationError({"rank_status": "Unranked tracks cannot have a tier or points."})
        return attrs
