This is the repository for **LinkWatcher**, a system that categorizes the anonymity of data in a web service's database, without dependence on the untrusted developer.

You can access the paper [here](https://dcollection.snu.ac.kr/common/orgView/000000184244)

## Problem Scenario
<img width="500" alt="Screenshot 2025-03-17 at 1 17 38 AM" src="https://github.com/user-attachments/assets/97abc78e-0e23-4165-9e6e-aa25386608c9" />

Suppose a user sends her personal data to an application, e-shop. Some of her data is more sensitive than others (ex. email vs age).
Her data is processed then stored in the application database.
How do we know the sensitivity of each data output to the application database? In other words, how do we know which of the user's input data flowed into which output data?
Only the developer really knows!

<img width="500" alt="Screenshot 2025-03-17 at 1 16 27 AM" src="https://github.com/user-attachments/assets/4f1d7a76-8a8c-4aea-893b-51eaf3aa76f1" />

This is a problem because privacy laws rely on the categorization of data: *is the data anonymous? or not?*
The auditor has no choice but to rely on the developer's categorization.

## LinkWatcher design
<img width="500" alt="Screenshot 2025-03-17 at 1 22 53 AM" src="https://github.com/user-attachments/assets/91443a60-fcf8-41af-a468-1b408b0dc7f3" />

LinkWatcher solves this problem with a system comprising two phases.

In the static phase, a static analyzer analyses dataflow of application code, identifies links (particular patterns of dataflow) that are formed, and outputs a summary of links.

In the runtime phase, the user sends her **data**, along with a **tag** that indicates sensitivity of the data, and a **token**.
The LinkWatcher middleware interposes between the application and any I/O to the user and the database.
When the application writes to the database, LinkWatcher dynamically analyses the sensitivity of data being written, based on tag, token, and summary of links.
By doing so LinkWatcher can automatically categorize whether a single piece of data in the application database is anonymous or identifiable, without relying on the malicious developer.


## Implementation
- Static Analyzer: modified version of pyt
    - Core dataflow analysis logic implemented in this file. Detects particular patterns of dataflow that form "links" in user data. Modified for analysis to be object/field sensitive.
      - pyt/pyt/analysis/definition_chains.py
    - Other files
      - pyt/pyt/cfg/stmt_visitor.py
      - pyt/pyt/analysis/reaching_definitions_taint.py
- Runtime Middleware: modified version of django
    - Interposing between application I/O to user
      - django/django/contrib/messages/middleware.py
      - django/django/core/handlers/base.py
      - django/django/core/handlers/wsgi.py
      - django/django/http/request.py
    - Interposing between DB I/O to user
      - django/django/db/backends/
      - django/django/db/models/
- Benchmarking (k6)
    - benchmarking/
- Example toy applications
    - django-ecommerce/
    - StackOverflow--Clone/
