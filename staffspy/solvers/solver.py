from abc import ABC,abstractmethod

class Solver(ABC):
    public_key = "3117BF26-4762-4F5A-8ED9-A85E69209A46"
    page_url = "https://iframe.arkoselabs.com"

    def __init__(self, solver_api_key:str):
        self.solver_api_key=solver_api_key

    @abstractmethod
    def solve(self, blob_data: str, page_ur: str=None):
        pass
