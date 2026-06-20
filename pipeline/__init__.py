"""Trace in, ranked hitch hypotheses out.

Stage order: ingest, detect, analyze, retrieve, reason. Stages exchange
plain serializable data so each one can be swapped out on its own.
"""
