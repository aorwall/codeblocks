import time
from typing import List, Any

from langchain.llms.base import create_base_retry_decorator

from ghostcoder.llm.base import LLMWrapper
from ghostcoder.schema import Message, Stats


class AlpacaLLMWrapper(LLMWrapper):

    def generate(self, sys_prompt: str, messages: List[Message]) -> (str, Stats):
        starttime = time.time()

        prompt_value = "### System Prompt\n" + sys_prompt + "\n\n"
        prompt_value += self.messages_to_prompt(messages)
        prompt_value += "\n\n### Assistant\n"

        retry_decorator = create_base_retry_decorator(error_types=[ValueError], max_retries=5)

        @retry_decorator
        def _completion_with_retry() -> Any:
            return self.llm.predict(prompt_value)

        result = _completion_with_retry()

        usage = Stats.from_dict(
            prompt=self.__class__.__name__,
            llm_output={},
            duration=time.time() - starttime)

        return result, usage

    def messages_to_prompt(self, messages: List[Message], few_shot_example: bool = False):
        llm_messages = ""

        for message in messages:
            if message.sender == "Human":
                llm_messages += "\n\n### User Message\n" + str(message)
            elif message.sender == "AI":
                llm_messages += "\n\n### Assistant\n" + str(message)
        return llm_messages
