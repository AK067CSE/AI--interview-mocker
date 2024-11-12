from openai import OpenAI

# Set up OpenAI client with Nvidia API base URL
client = OpenAI(
  base_url="https://integrate.api.nvidia.com/v1",
  api_key="nvidia api"
)

# Define prompt templates for different content types
AI_PROMPTS = {
    "analogy": """
    Explain [Concept] using an analogy with something familiar. Make it:
    - Easy to understand, avoiding technical terms or complexity
    - Based on a common experience or idea
    - Focused on key similarities and insights to make the concept relatable and clear.
    """,
    "description": """
    Break down [Concept] in a simple, beginner-friendly way. Imagine it's being introduced for the first time. Make it:
    - Brief, fun, and easy to follow
    - Focused on the main idea and basic functionality.
    """,
    "codeSnippet": """
    Create a concise code snippet to demonstrate [Programming Concept]. Make it:
    - Short (under 20 lines) and syntactically correct
    - Clear and practical, showcasing a specific use of the concept
    - Commented with brief explanations for readability
    Use [Programming Language] and provide a hands-on example for easy experimentation.
    """,
    "funfacts": """
    Make learning [Concept] exciting with fun facts. Find:
    - Intriguing or surprising details related to the concept
    - Simple and memorable explanations
    - Vivid descriptions or unexpected connections that spark curiosity
    List 2-3 engaging fun facts to enhance enjoyment and retention.
    """,
    "quiz": """
    Reinforce understanding of [Concept] with a short quiz. Include:
    - Key questions that cover the concept's essentials
    - Clear language and concise questions
    - Answers with brief explanations to deepen understanding
    Keep it engaging, informative, and balanced in difficulty.
    """,
    "assignment": """
    Design a mini assignment to apply [Concept] practically. Make it:
    - Simple and focused, taking under 30 minutes
    - Centered on one main aspect of the concept
    - Relevant to real-life or relatable scenarios
    Help reinforce understanding by creating a hands-on task to apply [Concept].
    """
}

# Define text prompt for content structure
TEXT_PROMPT = """\
Create a set of maximum {max_objects} card objects to provide {content_type} related to the subtopic "{subtopic}" of "{skill_name}" under the topic "{topic}".
Guidelines:
1. Card ID should follow the format: '{card_prefix}{{index}}-sub{{index}}' where the index starts from 1.
2. Each card's content should not exceed 6 lines. If needed, add additional content in a new card object.
3. The value of the content property should be of the same data type as provided in the schema/sample.
4. Use </br> after each sentence.
5. Use simple and easy-to-understand vocabulary.
6. Style content with HTML and inline styles for emphasis & key terms (e.g., <span style="color: red;">bold</span>, <span style="color: green;">colors</span>, <i>italic</i>).
7. Use only the element values available in the card render object.
8. If a {content_type} is irrelevant for the subtopic "{subtopic}" of "{skill_name}" under the topic "{topic}", provide output as an empty JSON object.
"""

CONTENT_TYPES_ARRAY = ["analogy", "description", "codeSnippet", "funfacts", "quiz", "assignment"]
MAX_OBJECTS = {
    "analogy": 1,
    "description": 8,
    "codeSnippet": 3,
    "funfacts": 2,
    "quiz": 6,
    "assignment": 1
}

# Function to get OpenAI response based on a prompt
def get_openai_response(prompt):
    completion = client.chat.completions.create(
        model="nvidia/nemotron-4-340b-instruct",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        top_p=0.7,
        max_tokens=1024,
        stream=True
    )

    response = ""
    for chunk in completion:
        if chunk.choices[0].delta.content is not None:
            response += chunk.choices[0].delta.content
    return response.strip()

# Function to get response and scores using Nvidia reward model
def get_response_and_scores(client, model, question, response_content):
    messages = [
        {
            "role": "user",
            "content": question
        },
        {
            "role": "assistant",
            "content": response_content
        },
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )

    scores = get_scores_from_response(response)
    return scores

# Function to get scores from response
def get_scores_from_response(openai_response_template):
    logprobs = openai_response_template.choices[0].logprobs.content
    score_dict = {}
    for score in logprobs:
        score_dict[score.token] = score.logprob
    return score_dict

# Function to process the question-response card pairs
def process_question_response_card_pairs(question_response_cards):
    # Initialize a list to store the processed question-response card pairs
    processed_question_response_card_pairs = []

    # Iterate over the question-response cards
    for question_response_card in question_response_cards:
        # Get the question and responses from the question-response card
        question = question_response_card["question_response"]["render"][0]["content"]["question"]
        response_a = question_response_card["question_response"]["render"][0]["content"]["responses"]["response_a"]
        response_b = question_response_card["question_response"]["render"][0]["content"]["responses"]["response_b"]

        # Get the scores for the responses using the Nvidia reward model
        score_a = get_response_and_scores(client, "nvidia/nemotron-4-340b-reward", question, response_a)["helpfulness"]
        score_b = get_response_and_scores(client, "nvidia/nemotron-4-340b-reward", question, response_b)["helpfulness"]

        # Add the processed question-response card pair to the list
        processed_question_response_card_pairs.append({
            "question": question,
            "response_a": response_a,
            "score_a": score_a,
            "response_b": response_b,
            "score_b": score_b
        })

    # Return the list of processed question-response card pairs
    return processed_question_response_card_pairs

# Function to generate array of subtopic objects with content
def generate_subtopic_array(subject):
    subtopic_array = []

    for subtopic in subject["subtopics"]:
        card_prefix = f"{subject['topic']}-{subtopic['name']}"

        for content_type in AI_PROMPTS.keys():
            if content_type in subtopic:
                # Combine AI_PROMPTS and TEXT_PROMPT for a detailed prompt
                prompt = (
                    TEXT_PROMPT.format(
                        max_objects=6,  # Define max number of objects if needed
                        content_type=content_type,
                        subtopic=subtopic["name"],
                        skill_name=subject["skill_name"],
                        topic=subject["topic"],
                        card_prefix=card_prefix
                    ) + AI_PROMPTS[content_type].replace("[Concept]", subtopic["name"])
                )

                response = get_openai_response(prompt)

                # Append content based on content_type to subtopic array
                if content_type == "analogy":
                    subtopic_array.append({
                        "analogy": {
                            "cardId": f"{card_prefix}_analogy",
                            "render": [
                                {"element": "analogy", "about": f"An analogy explaining {subtopic['name']}", "content": response}
                            ]
                        }
                    })
                elif content_type == "description":
                    subtopic_array.append({
                        "description": {
                            "cardId": f"{card_prefix}_description",
                            "render": [
                                {"element": "description", "about": f"Description of {subtopic['name']}", "content": response}
                            ]
                        }
                    })
                elif content_type == "codeSnippet":
                    subtopic_array.append({
                        "codeSnippet": {
                            "cardId": f"{card_prefix}_codeSnippet",
                            "render": [
                                {"element": "codeSnippet", "about": f"Code example for {subtopic['name']}", "content": response}
                            ]
                        }
                    })
                elif content_type == "funfacts":
                    subtopic_array.append({
                        "funfacts": {
                            "cardId": f"{card_prefix}_funfacts",
                            "render": [
                                {"element": "facts", "about": f"Fun facts about {subtopic['name']}", "content": response}
                            ]
                        }
                    })
                elif content_type == "quiz":
                    n_questions = 2
                    # Generate questions for the subtopic
                    QUESTION_PROMPT_TEMPLATE = """\
                    Given a topic, generate {n_questions} questions that could be asked about that topic. Your response should be in a list format.

                    The topic is: {sub_topic}

                    The list must be without numbers. The questions should be separated by a newline character. There must be no other text than the list.
                    """
                    question_prompt = QUESTION_PROMPT_TEMPLATE.format(sub_topic=subtopic["name"], n_questions=n_questions)
                    question_response = get_openai_response(question_prompt)
                    questions = [question.strip() for question in question_response.split("\n") if question]

                    # Generate responses for each question
                    RESPONSE_PROMPT_TEMPLATE = """\
                    Given a question, generate 2 responses that could be given to that question. Your response should be in a list format.

                    The question is: {question}

                    The list must be in the format:

                    RESPONSE A: Response A text here
                    RESPONSE B: Response B text here
                    """
                    quiz_content = []
                    question_response_pair_list = []
                    for question in questions:
                        response_prompt = RESPONSE_PROMPT_TEMPLATE.format(question=question)
                        response_set = get_openai_response(response_prompt)
                        response_a = response_set.split("RESPONSE B:")[0].replace("RESPONSE A:", "").strip()
                        response_b = response_set.split("RESPONSE B:")[-1].split("\n\n")[0].strip()

                        quiz_content.append({
                            "question": question,
                            "responses": {
                                "response_a": response_a,
                                "response_b": response_b
                            }
                        })

                        question_response_pair_list.append(
                            {
                                "question": question,
                                "responses": {
                                    "response_a": {"response": response_a},
                                    "response_b": {"response": response_b}
                                },
                            }
                        )

                    subtopic_array.append({
                        "quiz": {
                            "cardId": f"{card_prefix}_quiz",
                            "render": [
                                {"element": "quiz", "about": f"Quiz on {subtopic['name']}", "content": quiz_content}
                            ]
                        }
                    })

                    # Generate question-response cards
                    question_response_cards = []
                    for i, question_response in enumerate(quiz_content):
                        question_response_cards.append({
                            "question_response": {
                                "cardId": f"{card_prefix}_question_response_{i+1}",
                                "render": [
                                    {"element": "question_response", "about": f"Question-response card {i+1} for {subtopic['name']}", "content": question_response}
                                ]
                            }
                        })

                    subtopic_array.extend(question_response_cards)

                    # Score the responses
                    question_response_score_list = process_question_response_card_pairs(question_response_cards)

                    # Add the scores to the question-response cards and print them
                    for i, question_response in enumerate(question_response_score_list):
                        question_response_cards[i]["question_response"]["render"][0]["score"] = {
                            "response_a": question_response["score_a"],
                            "response_b": question_response["score_b"]
                        }
                        # Print the card responses with scores
                        print(f"Question: {question_response['question']}")
                        print(f"Response A: {question_response['response_a']} (Score: {question_response['score_a']})")
                        print(f"Response B: {question_response['response_b']} (Score: {question_response['score_b']})\n")
                elif content_type == "assignment":
                    subtopic_array.append({
                        "assignment": {
                            "cardId": f"{card_prefix}_assignment",
                            "render": [
                                {"element": "assignment", "about": f"Assignment for {subtopic['name']}", "content": response}
                            ]
                        }
                    })
    return subtopic_array

# Sample subject input to test the function
subject = {
    "topic": "GPU Computing",
    "skill_name": "Advanced Computing Skills",
    "subtopics": [
        {"name": "Parallel Processing", "analogy": True,  "assignment": True},
        {"name": "CUDA Programming", "analogy": True, "codeSnippet": True, "quiz": True},
    ]
}

# Generate the subtopic array with responses
subtopic_cards = generate_subtopic_array(subject)

# Print the generated cards for inspection
for card in subtopic_cards:
    print(card)
