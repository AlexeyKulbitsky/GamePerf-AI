# KB v0.1

One JSON file per hitch pattern:

    {
      "id": "slug",
      "title": "...",
      "engines": ["godot", "unreal", "any"],
      "symptoms": ["what the retriever matches on"],
      "mechanism": "why it hitches",
      "diagnosis_hints": "how to confirm or rule out",
      "typical_fixes": ["..."],
      "sources": ["public references only"]
    }

Starter set (10 entries): GC spike, physics burst, sync asset load, runtime
shader compile, N^2 collision, spawn burst, alloc churn, serialization
stall, event storm, scene-tree traversal.
