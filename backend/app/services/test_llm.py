from app.services.llm_service import generate_answer


answer = generate_answer(
    question="What is the coffee machine?",
    context="""
    CoffeeMaker Class

    Methods:
    - report(): Prints a report of all resources.
    - is_resource_sufficient(drink): Checks whether there are
      enough ingredients to make a drink.
    - make_coffee(order): Deducts the required ingredients
      from the resources.
    """
)

print("\n" + "=" * 60)
print("LLM ANSWER")
print("=" * 60)
print(answer)