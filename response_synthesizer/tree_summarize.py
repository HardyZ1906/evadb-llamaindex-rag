from openai_utils import llm_call
from response_synthesizer.base import BaseResponseSynthesizer
from response_synthesizer.compact import DEFAULT_QA_PROMPT_TEMPLATE

DEFAULT_SUMMARY_PROMPT_TEMPLATE = """
Below is a question:
-----------------------------------------------------------
{question}
-----------------------------------------------------------

We already have several existing answers, each of which is
concluded based on partial and distinct context information:
-----------------------------------------------------------
{answers}
-----------------------------------------------------------

Assuming no prior knowledge and based on these answers ONLY,
please answer the question.
Briefly justify your answer in one or two sentences.
"""

class TreeSummarizeResponseSynthesizer(BaseResponseSynthesizer):
  """In each round, feed the LLM text chunks in fixed sized batches as context information;
  If more than one answer were produced in the last round, use those answers as new text chunks
  and continue consulting the LLM
  """
  
  def __init__(self, model: str = "gpt-3.5-turbo-1106", batch_size: int = 2,
               qa_prompt: str = DEFAULT_QA_PROMPT_TEMPLATE,
               summary_prompt: str = DEFAULT_SUMMARY_PROMPT_TEMPLATE) -> None:
    super().__init__(model)
    self.batch_size = batch_size
    self.qa_prompt = qa_prompt
    self.summary_prompt = summary_prompt

  def synthesize(self, question: str, context: [str]) -> (str, int):
    total_cost = 0
    
    answers = []
    for i in range(0, len(context), self.batch_size):
      prompt = self.qa_prompt.format(question = question, context = "\n".join(context[i : i+self.batch_size]))
      # print(prompt)
      response, cost = llm_call(model = self.model, user_prompt = prompt)
      ans = response["choices"][0]["message"]["content"]
      # print(ans)
      answers.append(ans)
      total_cost += cost
    
    while len(answers) > 1:
      new_answers = []
      for i in range(0, len(answers), self.batch_size):
        if i == len(answers) - 1:
          continue
        prompt = self.summary_prompt.format(question = question, answers = "\n".join(answers[i : i+self.batch_size]))
        # print(prompt)
        response, cost = llm_call(model = self.model, user_prompt = prompt)
        ans = response["choices"][0]["message"]["content"]
        # print(ans)
        new_answers.append(ans)
        total_cost += cost
      answers = new_answers
    
    return answers[0], total_cost