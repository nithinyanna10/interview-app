#!/usr/bin/env python3
"""Simple Flask API exposing a stub equation solver."""

from __future__ import annotations

import os
from flask import Flask, jsonify, request
from sympy import sympify, solve as sympy_solve, SympifyError


def create_app() -> Flask:
    app = Flask(__name__)

    @app.after_request
    def add_cors_headers(response):  # type: ignore[override]
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    @app.get("/solve")
    def solve():
        equation = (request.args.get("equation") or "").strip()
        if not equation:
            return jsonify({"error": "Missing 'equation' query parameter"}), 400
        
        try:
            # Normalize the equation: replace ^ with ** for Python exponentiation
            equation_normalized = equation.replace("^", "**")
            
            # Parse the equation
            # Handle cases where equation might be in form "expression = 0" or just "expression"
            if '=' in equation_normalized:
                # Split by = and move everything to one side
                parts = equation_normalized.split('=', 1)
                left = sympify(parts[0].strip(), evaluate=False)
                right = sympify(parts[1].strip(), evaluate=False)
                expr = left - right
            else:
                # Assume expression = 0
                expr = sympify(equation_normalized, evaluate=False)
            
            # Extract variables from the expression
            free_symbols = expr.free_symbols
            if not free_symbols:
                return jsonify({"error": "No variable found in equation"}), 400
            
            # Use the first variable found (or 'x' if available, otherwise first alphabetically)
            var = None
            for v in sorted(free_symbols, key=str):
                if str(v) == 'x':
                    var = v
                    break
            if var is None:
                var = sorted(free_symbols, key=str)[0]
            
            var_name = str(var)
            
            # Solve the equation
            solutions = sympy_solve(expr, var)
            
            if not solutions:
                return jsonify({"result": "No solution found"})
            
            # Format the solutions
            if len(solutions) == 1:
                solution = solutions[0]
                # Convert to float if it's a number, otherwise keep symbolic
                if solution.is_number:
                    result_str = f"{var_name} = {float(solution):.6f}".rstrip('0').rstrip('.')
                else:
                    result_str = f"{var_name} = {solution}"
            else:
                # Multiple solutions
                solution_strs = []
                for sol in solutions:
                    if sol.is_number:
                        sol_str = f"{float(sol):.6f}".rstrip('0').rstrip('.')
                    else:
                        sol_str = str(sol)
                    solution_strs.append(sol_str)
                result_str = f"{var_name} = {', '.join(solution_strs)}"
            
            return jsonify({"result": result_str})
            
        except SympifyError as e:
            return jsonify({"error": f"Invalid equation format: {str(e)}"}), 400
        except Exception as e:
            return jsonify({"error": f"Error solving equation: {str(e)}"}), 500

    @app.route("/", methods=["GET"])
    def root():
        return jsonify({"message": "Equation API. Try /solve?equation=1+1"})

    return app


def run() -> None:
    port = int(os.environ.get("PORT", 8000))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    run()
