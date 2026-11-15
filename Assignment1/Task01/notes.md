# Task 1 - Cloud Computing and the Smart Campus Scenario

Labels: [G] given in the question paper, [A] assumed, [T] typical published idea.

## 1. Definition
Cloud computing is a model where computing resources (servers, storage, networks, platforms, software) are rented over the internet, on demand, from a shared pool, and paid for by use instead of being bought and owned. [T: NIST-style definition, in my own words]

## 2. Five essential characteristics
| Characteristic | Meaning | University example |
|---|---|---|
| On-demand self-service | I create resources myself, with no ticket or purchase order | IT staff starts a new server for the exam portal in minutes |
| Broad network access | Services reachable by browser, phone, API | Students use the portal from any campus or home |
| Resource pooling | Many customers share one big pool, virtually divided | Admissions load and idle library load share the same hardware |
| Rapid elasticity | Capacity grows and shrinks automatically | Extra servers during results week, released afterwards |
| Measured service | Usage is metered and billed | Pay only for the exam-week peak |

## 3. Deployment models
| Model | Who uses it | Fit for the university |
|---|---|---|
| Public | Anyone, provider owns hardware | Cheap and elastic; good for portal, LMS, email |
| Private | One organisation only | Full control, but the university again buys hardware (same CapEx problem) |
| Hybrid | Public + private joined | Sensitive records stay private, peaks go to public |
| Community | Several organisations with shared needs | Possible later for the 40 affiliated colleges |

Suitable choice: HYBRID, mostly public. Reason: the problems are peaks and cost (public cloud solves these), but student records are sensitive and the old servers cannot be switched off on day one, so some systems stay on-premise during migration. [A: this is my design decision; Task 10 will justify it with costs]

## 4. Three problems of the current setup and how the cloud answers
Given facts [G]: 12 physical servers, about 15% average CPU, peaks above 95%, 25,000 students and 2,000 staff, 4 campuses, 6-8 weeks to buy a server, no disaster recovery site.

| Problem [G] | Cloud characteristic that addresses it | How |
|---|---|---|
| Servers idle at about 15% but crash at 95%+ peaks in admissions and exams | Rapid elasticity + resource pooling | Capacity follows load; idle capacity is not paid for |
| High capital cost and 6-8 weeks to get a server | On-demand self-service + measured service | New resources in minutes, pay-per-use OpEx instead of CapEx |
| Single data centre, no disaster recovery, no mobile or partner access | Broad network access (plus provider multi-region) | Services reachable over the internet; data can be copied to a second region |

## 5. Benefits and limitations for the university
Benefits: lower upfront cost, handles peaks, faster rollout, DR becomes affordable, less hardware maintenance, easier mobile and partner access.
Limitations: ongoing monthly bills that can grow if unmanaged, vendor lock-in, student data privacy and legal location of data, dependence on internet connection, staff need new skills, migration effort for the monolithic applications.

## 6. Viva points
- NIST five characteristics: self-service, network access, pooling, elasticity, measured.
- Why hybrid and not full public: sensitive data and gradual migration.
- Which problem each characteristic fixes (table in section 4).
