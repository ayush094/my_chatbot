from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .services.json_ai import (
    generate_json_plan,
    generate_natural_answer
)
from .services.json_validator import validate_json
from .services.sql_builder import build_sql
from .services.sql_executor import execute_sql
from .models import ChatMessage


def chat_home(request):
    """
    Renders the chatbot UI
    """
    return render(request, "chat/index.html")


@method_decorator(csrf_exempt, name="dispatch")
class ChatAPIView(APIView):
    """
    Main Chat API:
    User Question → AI JSON Plan → Validation → SQL → Answer
    """
    permission_classes = [AllowAny]
    authentication_classes = []  # CSRF disabled for local/dev usage

    def post(self, request):
        message = request.data.get("message")

        if not message or not isinstance(message, str):
            return Response(
                {"error": "Message is required"},
                status=400
            )

        try:
            #  Natural Language → JSON Query Plan
            plan = generate_json_plan(message)

            #  Validate JSON Plan (Security Gate)
            if not validate_json(plan):
                return Response(
                    {
                        "answer": (
                            "Sorry, I couldn’t safely understand this request "
                            "or it attempts to access unauthorized data."
                        )
                    },
                    status=400,
                )

            #  JSON → SQL
            sql, params = build_sql(plan)

            if not sql:
                return Response(
                    {
                        "answer": (
                            "Sorry, this query could not be executed safely."
                        )
                    },
                    status=400,
                )

            #  Execute SQL
            rows = execute_sql(sql, params)

            #  SQL Result → Natural Language Answer
            answer = generate_natural_answer(message, rows)

            #  Save Chat History
            ChatMessage.objects.create(
                user_message=message,
                ai_response=answer
            )
            


            return Response(
                {
                    "answer": answer
                    # Intentionally NOT returning SQL in prod
                },
                status=200,
            )

        except Exception as e:
            # Controlled Error Handling
        
            import traceback
            traceback.print_exc()

            return Response(
                {
                    "answer": "An internal error occurred while processing your request."
                },
                status=500,
            )
