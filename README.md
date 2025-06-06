This is the repository for **LinkWatcher**, a system that categorizes the anonymity of data in a web service's database, without dependence on the untrusted developer.

You can access the paper [here](https://dcollection.snu.ac.kr/common/orgView/000000184244)

## Problem Scenario
<img width="500" alt="Problem Scenario" src="./img/problem_scenario.png" />

Suppose a user sends her personal data to an application, e-shop. Some of her data is more sensitive than others (ex. email vs age).
Her data is processed then stored in the application database.
How do we know the sensitivity of each data output to the application database? In other words, how do we know which of the user's input data flowed into which output data?
Only the developer really knows!

<img width="500" alt="LinkWatcher background" src="./img/problem_scenario2.png" />

This is a problem because privacy laws rely on the categorization of data: *is the data anonymous? or not?*
The auditor has no choice but to rely on the developer's categorization.

## LinkWatcher design
<img width="500" alt="LinkWatcher design" src="./img/deisgn.png" />

LinkWatcher solves this problem with a system comprising two phases.

In the static phase, a static analyzer analyses dataflow of application code, identifies links (particular patterns of dataflow) that are formed, and outputs a summary of links.

In the runtime phase, the user sends her **data**, along with a **tag** that indicates sensitivity of the data, and a **token**.
The LinkWatcher middleware interposes between the application and any I/O to the user and the database.
When the application writes to the database, LinkWatcher dynamically analyses the sensitivity of data being written, based on tag, token, and summary of links.
By doing so LinkWatcher can automatically categorize whether a single piece of data in the application database is anonymous or identifiable, without relying on the malicious developer.
LinkWatcher stores these analysis results in a Linkage database, and returns it to the user.

## How is the LinkWatcher static analyzer different from other analyzers?

The LinkWatcher static analyzer modifies [pyt](https://github.com/python-security/pyt) to track dataflow that harms anonymity by:
1. Implementing field senstiive data analysis
2. Multi-source, multi-sink analysis (as there can be multiple database reads and writes in a single user request)
3. Incorporating both forward & backward analysis
    - to effectively identify *Links* formed by dataflow in code
    - *Links* are formed when:
        - user data (source) flows to a sink
        - user data and *any* variable (including constant variables) act as operands together in a variable assignment.
        - such *any* variable flows to a sink.

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
- Linkage Database
    - uses neo4j
