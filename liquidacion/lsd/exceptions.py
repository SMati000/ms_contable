class ErroresGeneracionLsd(Exception):
    def __init__(self, errores):
        self.errores = tuple(errores)
        super().__init__("\n".join(f"• {error}" for error in self.errores))
