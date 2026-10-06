// Generated from public/resources/sovereign-workbench-terms-v1.0.docx. Do not edit by hand:
// regenerate from the document so the in-app text and the downloadable original never diverge.
// termsModel.test.js pins DOCX_SHA256; a changed document fails the test until this file is regenerated.
export const DOCX_SHA256 = 'feef43e2378f40e48cd9cd5449d121c56fb2f9bd4dc47e860c87a8db2735bc6f'
export const TERMS_V1 = {
 "version": "1.0",
 "title": "Terms & Conditions and Acceptable Use Policy",
 "sections": [
  {
   "heading": "Acceptance of Terms",
   "blocks": [
    {
     "text": "By logging in, accessing or using the Sovereign On-Premise Agentic AI Workbench (the \"Application\"), you acknowledge that you have read, understood, and agree to be bound by these Terms & Conditions and the Acceptable Use Policy. If you do not agree, you must not use the Application. Continued use after an update to these terms constitutes acceptance of the updated terms."
    }
   ]
  },
  {
   "heading": "1. Nature and Purpose of the Application",
   "blocks": [
    {
     "text": "The Application is a private, company-controlled industrial AI workbench for MRPL-style refinery environments. It provides advisory capabilities including knowledge retrieval, multimodal evidence (documents, P&ID/OCR, sensors, maintenance history), grounded reasoning with citations, multi-agent orchestration, and tamper-evident audit."
    },
    {
     "text": "The Application is an advisory and information-retrieval tool only.",
     "lead": "CRITICAL RULE:"
    },
    {
     "text": "The Application may advise, retrieve, compare, summarize and reason; it never directly starts, stops, isolates, bypasses, or otherwise controls plant equipment. The Application has no live SCADA/DCS write capability and no plant-execution authority.",
     "lead": "AI NEVER CONTROLS EQUIPMENT:"
    }
   ]
  },
  {
   "heading": "2. Advisory Use and Human Authority",
   "blocks": [
    {
     "list": true,
     "items": [
      {
       "text": "All outputs of the Application are advisory in nature and must be independently verified by a qualified engineer or authorized personnel before any operational, maintenance, or safety decision."
      },
      {
       "text": "Action-adjacent recommendations require review and approval by an authorized human (Plant Operations Head / Shift-in-Charge) through the human-in-the-loop governance workflow. The AI cannot approve its own recommendations."
      },
      {
       "text": "Approval releases only a reviewed advisory recommendation — never a plant-control command."
      },
      {
       "text": "The user accepts full responsibility for decisions taken based on AI outputs, in accordance with company procedure and applicable regulations."
      }
     ]
    }
   ]
  },
  {
   "heading": "3. Acceptable Use",
   "blocks": [
    {
     "text": "You agree to use the Application only for legitimate, authorized, work-related purposes. You must NOT:"
    },
    {
     "list": true,
     "items": [
      {
       "text": "Use the Application to attempt to start, stop, isolate, bypass, or control any plant equipment."
      },
      {
       "text": "Enter requests intended to bypass deterministic safety, domain, access-scope, or injection-prevention gates."
      },
      {
       "text": "Attempt prompt-injection, jailbreaking, data exfiltration, or circumvention of RBAC or audit logging."
      },
      {
       "text": "Upload malicious files or content designed to disrupt the system or mislead other users or agents."
      },
      {
       "text": "Use OCR or image-derived evidence as standalone proof of plant topology, isolation status, or valve state."
      },
      {
       "text": "Represent AI-generated content as verified plant truth without human confirmation and citation-backed evidence."
      },
      {
       "text": "Access data outside your authorized role/scope (least-privilege applies)."
      }
     ]
    }
   ]
  },
  {
   "heading": "4. Data, Privacy and Sovereignty",
   "blocks": [
    {
     "list": true,
     "items": [
      {
       "text": "All data (documents, drawings, sensor data, queries, outputs) is processed and stored inside company-controlled infrastructure. No hosted OpenAI/Gemini/Anthropic inference is used."
      },
      {
       "text": "The Application provides application-level sovereignty checks (local model/runtime and database validation); it does not replace company firewall or network policy."
      },
      {
       "text": "Your queries, sessions, approvals, and agent interactions may be recorded in a hash-chained, tamper-evident audit log for governance, safety, and compliance purposes."
      },
      {
       "text": "Administrators may review audit records in accordance with company policy. Do not enter personal data beyond what is necessary for your role."
      },
      {
       "text": "Shift notes and tacit knowledge submitted may be structured into institutional memory and retrieved by other authorized users, with provenance preserved."
      }
     ]
    }
   ]
  },
  {
   "heading": "5. Evidence, Citations and Limitations",
   "blocks": [
    {
     "list": true,
     "items": [
      {
       "text": "The Application is designed to ground answers in retrievable evidence with citations. However, retrieved evidence may be incomplete, outdated, or misread (especially OCR-derived content)."
      },
      {
       "text": "The system may refuse to answer when evidence is insufficient (missing-evidence refusal). This is intended behavior, not a malfunction."
      },
      {
       "text": "The current build is validated with synthetic/public-style industrial data, not confidential live plant data. It must not be treated as certified for live operational decision-making until formally approved by the company."
      },
      {
       "text": "Known limitation: full agentic responses may have high latency; fast/verified paths may be used where available."
      }
     ]
    }
   ]
  },
  {
   "heading": "6. Intellectual Property",
   "blocks": [
    {
     "list": true,
     "items": [
      {
       "text": "Company knowledge sources (SOPs, manuals, P&IDs, records) remain the property of the company."
      },
      {
       "text": "The Application software stack (integration, agents, UI) is developed for the SIH26117 project. Rights are as agreed between the team and the company."
      },
      {
       "text": "Verified Knowledge Registry entries are version-bound; when source documents change, previously verified answers automatically become stale and must not be reused without re-verification."
      }
     ]
    }
   ]
  },
  {
   "heading": "7. Security and Access",
   "blocks": [
    {
     "list": true,
     "items": [
      {
       "text": "Access is role-based and authenticated. You must not share credentials or allow unauthorized persons to use your session."
      },
      {
       "text": "The deterministic preflight gate (domain, scope, injection, unsafe-action checks) runs before any AI reasoning and cannot be overridden by users or agents."
      },
      {
       "text": "Any attempt to tamper with, disable, or evade audit/evidence integrity is prohibited and will be logged and reported."
      }
     ]
    }
   ]
  },
  {
   "heading": "8. Disclaimers and Warranties",
   "blocks": [
    {
     "text": "THE APPLICATION IS PROVIDED \"AS IS\" AND \"AS AVAILABLE\". TO THE MAXIMUM EXTENT PERMITTED BY LAW, THE APPLICATION DISCLAIMS ALL WARRANTIES, EXPRESS OR IMPLIED, INCLUDING MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT. AI OUTPUTS MAY CONTAIN ERRORS, OMISSIONS, OR OUTDATED INFORMATION AND ARE NOT A SUBSTITUTE FOR PROFESSIONAL ENGINEERING JUDGMENT, COMPANY PROCEDURES, OR REGULATORY REQUIREMENTS."
    }
   ]
  },
  {
   "heading": "9. Limitation of Liability",
   "blocks": [
    {
     "list": true,
     "items": [
      {
       "text": "In no event shall the Application, its developers, or the company be liable for indirect, incidental, consequential, special, or punitive damages arising from use of or inability to use the Application."
      },
      {
       "text": "The company and its personnel retain sole authority and responsibility for plant operations. The Application does not assume any duty of care regarding plant safety or production."
      },
      {
       "text": "Nothing in these terms limits liability that cannot be limited by applicable law."
      }
     ]
    }
   ]
  },
  {
   "heading": "10. Modifications to the Application and Terms",
   "blocks": [
    {
     "text": "The company/development team may update the Application and these Terms & Conditions at any time. Material changes will be communicated through the Application or company channels. Continued use after the effective date of changes constitutes acceptance."
    }
   ]
  },
  {
   "heading": "11. Termination and Enforcement",
   "blocks": [
    {
     "list": true,
     "items": [
      {
       "text": "Access may be suspended or revoked at any time for policy violations, security risks, or role changes."
      },
      {
       "text": "Violations of these terms (especially attempts to bypass safety gates or misuse audit/evidence integrity) may result in disciplinary action under company policy and applicable law."
      }
     ]
    }
   ]
  },
  {
   "heading": "12. Governing Framework",
   "blocks": [
    {
     "text": "These terms are governed by the internal IT/IS policy of the deploying company and applicable laws of India. Disputes will be handled through company grievance/administrative channels unless otherwise required by law."
    }
   ]
  },
  {
   "heading": "13. Acceptance Mechanism in the Application",
   "blocks": [
    {
     "text": "On first login (and after any material update), users will be presented with:"
    },
    {
     "list": true,
     "items": [
      {
       "text": "A summary of key terms with mandatory checkboxes (e.g., \"I understand AI outputs are advisory only\", \"I will not attempt to bypass safety gates\", \"I accept audit logging of my activity\")."
      },
      {
       "text": "A scrollable full-text Terms & Conditions view with a timestamped \"Accept\" action recorded in the tamper-evident audit chain."
      },
      {
       "text": "A link to this document and version history of terms."
      }
     ]
    },
    {
     "text": "The acceptance event (user, timestamp, terms version, IP/hostname) is stored in the audit chain to prove informed consent.",
     "lead": "Audit note:"
    }
   ]
  },
  {
   "heading": "Appendix — Quick Summary for Users",
   "blocks": [
    {
     "text": "1. AI advises; humans decide. Never act on AI output without verification and required approval."
    },
    {
     "text": "2. The AI cannot and must not control any equipment."
    },
    {
     "text": "3. Your activity is audit-logged. Do not attempt to bypass safety or access controls."
    },
    {
     "text": "4. All data stays inside company infrastructure — do not paste it into public AI services."
    },
    {
     "text": "5. Citations and evidence must be checked; OCR evidence is not proof of plant state."
    }
   ]
  }
 ]
}
