from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist

from .models import ChatMessage, Employee, Leave
from .services.json_ai import generate_json_plan
from .services.json_validator import validate_json
from .services.sql_builder import build_sql
from .services.sql_executor import execute_sql
from .services.natural_answer import generate_natural_answer


def chat_home(request):
    """
    Renders the chatbot UI
    """
    return render(request, "chat/index.html")


from rest_framework.authentication import SessionAuthentication, BasicAuthentication

class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    SessionAuthentication but without CSRF enforcement for development.
    """
    def enforce_csrf(self, request):
        return

@method_decorator(csrf_exempt, name="dispatch")
class ChatAPIView(APIView):
    """
    Main Chat API:
    READ  → AI JSON → SQL → Answer
    WRITE → AI JSON → Action Handler
    """
    permission_classes = [AllowAny]
    authentication_classes = [CsrfExemptSessionAuthentication, BasicAuthentication]

    def post(self, request):
        message = request.data.get("message")
        if not message or not isinstance(message, str):
            return Response({"answer": "Message is required"}, status=400)

        # -------------------------------
        # 👤 Robust Identity Resolution
        # -------------------------------
        employee = None
        if request.user.is_authenticated:
            # Match by Email OR Username (case-insensitive) for dev flexibility
            employee = Employee.objects.filter(email__iexact=request.user.email).first()
            print("USER EMAIL:", request.user.email)


            if employee:
                print(f"DEBUG: Authenticated {request.user.username} as {employee.first_name} (ID: {employee.id})")
            else:
                print(f"DEBUG: Authenticated user '{request.user.username}' has no matching Employee record.")
        else:
            print("DEBUG: Request is Anonymous (Not logged in).")

        user_context = {}
        if employee:
            user_context = {
                "id": employee.id,
                "name": f"{employee.first_name} {employee.last_name}",
                "email": employee.email,
                "position": employee.position,
            }


        try:
            # -------------------------------
            # Natural Language → JSON Plan
            # -------------------------------
            plan = generate_json_plan(message, user_context=user_context)




            # -------------------------------
            # Validate JSON (Security Gate)
            # -------------------------------
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

            # ==================================================
            # 🔥 ACTION HANDLING (Approve / Deny Leave)
            # ==================================================
            if plan.get("action") == "approve_leave":
                leave_id = plan.get("leave_id")

                if not leave_id:
                    return Response({"answer": "Please specify a leave ID to approve."}, status=400)

                if not employee:
                    return Response({"answer": "I couldn't verify your identity. Please log in to your account to perform this action."}, status=403)

                try:
                    # Resolve leave and hierarchy in one go
                    leave = Leave.objects.select_related("employee__manager").get(id=leave_id)

                    # Security checks
                    if leave.employee == employee:
                        return Response({"answer": "You cannot approve your own leave."}, status=403)

                    if leave.employee.manager != employee:
                        return Response({"answer": "You are not authorized to approve this leave."}, status=403)

                    # Perform update
                    leave.status = "Approved"
                    leave.save()

                    answer = f"✅ Leave ID {leave_id} approved successfully."

                except (ObjectDoesNotExist, Leave.DoesNotExist):
                    return Response({"answer": "Leave request not found."}, status=404)

                except Exception as e:
                    print(f"APPROVE ERROR: {e}")
                    return Response({"answer": "Internal error while approving leave."}, status=500)

                # Save chat history
                ChatMessage.objects.create(user_message=message, ai_response=answer)
                return Response({"answer": answer}, status=200)


            # ==================================================
            # READ-ONLY FLOW (SQL SELECT)
            # ==================================================
            sql, params = build_sql(plan)

            if not sql:
                return Response(
                    {"answer": "Sorry, this query could not be executed safely."},
                    status=400,
                )

            rows = execute_sql(sql, params)

            answer = generate_natural_answer(message, rows)

            ChatMessage.objects.create(
                user_message=message,
                ai_response=answer,
            )

            return Response({"answer": answer}, status=200)

        except Exception as e:
            import traceback
            traceback.print_exc()

            # Handle Groq Rate Limits
            if "rate_limit_exceeded" in str(e).lower():
                return Response(
                    {"answer": "The AI is currently busy (rate limit reached). Please try again in a few minutes."},
                    status=429
                )

            return Response(
                {"answer": "An internal error occurred while processing your request."},
                status=500,
            )

