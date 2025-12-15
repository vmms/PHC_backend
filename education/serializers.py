from rest_framework import serializers
from .models import Education

class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = ['id_education', 
                  'country', 
                  'education', 
                  'graduation_year', 
                  'institute', 
                  'education_field'
                 ]