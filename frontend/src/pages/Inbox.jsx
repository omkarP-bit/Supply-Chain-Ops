import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import Layout from '../components/Layout';
import { Card, Button } from '../components/UI';

const INITIAL_EMAILS = [
  // 12 INBOX EMAILS
  {
    id: 'em-1',
    folder: 'inbox',
    sender: 'Apex Auto Parts',
    senderEmail: 'procurement@apexautoparts.example',
    recipient: 'procurement@scops.example',
    subject: 'Delay on PO-7712',
    snippet: 'Due to unexpected transportation issues, the delivery for PO-7712 may be delayed by approximately 5 days...',
    body: `Hello Procurement Team,

Due to unexpected transportation issues, the delivery for PO-7712 may be delayed by approximately 5 days.

The original expected delivery date was September 4. Our current estimated delivery is September 9.

We are checking whether a partial shipment can be arranged and will provide an update shortly.

Regards,
Apex Auto Parts`,
    timestamp: 'Today, 02:14 AM',
    timeShort: '2:14 AM',
    isRead: false,
    isStarred: true,
    hasAttachment: false,
    isAiAgent: false,
    tag: 'SUPPLIER DELAY',
  },
  {
    id: 'em-2',
    folder: 'inbox',
    sender: 'Apex Auto Parts',
    senderEmail: 'procurement@apexautoparts.example',
    recipient: 'procurement@scops.example',
    subject: 'Updated ETA for PO-7712',
    snippet: 'We have reviewed the shipment status for PO-7712. The revised estimated delivery date is September 9...',
    body: `Hello,

We have reviewed the shipment status for PO-7712.

The revised estimated delivery date is September 9. We currently cannot guarantee an earlier full shipment.

We will notify you if the transportation situation improves.

Regards,
Apex Auto Parts`,
    timestamp: 'Yesterday, 06:30 PM',
    timeShort: '6:30 PM',
    isRead: true,
    isStarred: false,
    hasAttachment: false,
    isAiAgent: false,
    tag: 'REVISED ETA',
  },
  {
    id: 'em-3',
    folder: 'inbox',
    sender: 'Apex Auto Parts',
    senderEmail: 'procurement@apexautoparts.example',
    recipient: 'procurement@scops.example',
    subject: 'Partial Shipment Option – PO-7712',
    snippet: 'We can arrange a partial shipment of 300 Brake Pads within 3 days. The remaining quantity would follow...',
    body: `Hello Procurement Team,

We can arrange a partial shipment of 300 Brake Pads within 3 days.

The remaining quantity would follow on the revised September 9 delivery schedule.

Please confirm if you would like us to proceed.

Regards,
Apex Auto Parts`,
    timestamp: 'Yesterday, 04:15 PM',
    timeShort: '4:15 PM',
    isRead: true,
    isStarred: false,
    hasAttachment: false,
    isAiAgent: false,
    tag: 'PARTIAL SHIPMENT',
  },
  {
    id: 'em-4',
    folder: 'inbox',
    sender: 'PrimeDrive Components',
    senderEmail: 'sales@primedrivecomponents.example',
    recipient: 'procurement@scops.example',
    subject: 'RFQ Response – Brake Pad',
    snippet: 'Thank you for your urgent RFQ. We can provide 600 Brake Pads at unit price ₹132, lead time 4 days...',
    body: `Hello,

Thank you for your urgent RFQ.

We can provide 600 Brake Pads.

Unit price: ₹132
Lead time: 4 days
Minimum order quantity: 300 units
Expedited shipping: Available

Our quoted availability is valid for 6 hours.

Regards,
PrimeDrive Components`,
    timestamp: 'Today, 02:11 AM',
    timeShort: '2:11 AM',
    isRead: false,
    isStarred: true,
    hasAttachment: true,
    isAiAgent: false,
    tag: 'ALTERNATE QUOTE',
  },
  {
    id: 'em-5',
    folder: 'inbox',
    sender: 'Nova Mobility Parts',
    senderEmail: 'support@novamobility.example',
    recipient: 'procurement@scops.example',
    subject: 'Certification Details – Brake Pad Supply',
    snippet: 'We can supply the requested Brake Pads within 3 days. However, our batch does not carry required automotive-grade cert...',
    body: `Hello,

We can supply the requested Brake Pads within 3 days.

However, our current production batch does not carry the required automotive-grade certification (ISO/TS 16949).

Please confirm whether an exception has been approved before placing an order.

Regards,
Nova Mobility Parts`,
    timestamp: 'Today, 01:58 AM',
    timeShort: '1:58 AM',
    isRead: true,
    isStarred: false,
    hasAttachment: false,
    isAiAgent: false,
    tag: 'QUALITY CONSTRAINT',
  },
  {
    id: 'em-6',
    folder: 'inbox',
    sender: 'Apex Auto Parts',
    senderEmail: 'tracking@apexautoparts.example',
    recipient: 'procurement@scops.example',
    subject: 'Shipment Tracking Update – PO-7712',
    snippet: 'PO-7712 has been dispatched from our facility. Tracking information has been updated in the shipment system...',
    body: `Hello,

PO-7712 has been dispatched from our facility.

Tracking information has been updated in the shipment system.

Regards,
Apex Auto Parts

---
Carrier Tracking Reference: AEX-992014
Current Carrier Telemetry: Label Created (Pickup Not Confirmed)`,
    timestamp: 'Today, 01:45 AM',
    timeShort: '1:45 AM',
    isRead: false,
    isStarred: false,
    hasAttachment: false,
    isAiAgent: false,
    tag: 'CLAIM CONTRADICTION',
  },
  {
    id: 'em-7',
    folder: 'inbox',
    sender: 'Precision Auto Systems',
    senderEmail: 'orders@precisionauto.example',
    recipient: 'procurement@scops.example',
    subject: 'Availability Confirmation – Battery Controller',
    snippet: 'We currently have 350 Battery Controllers available for immediate shipment. We cannot fulfill complete 600 units from stock...',
    body: `Hello,

We currently have 350 Battery Controllers available for immediate shipment.

We cannot fulfill the complete requested quantity of 600 units from current stock.

The remaining quantity would require approximately 8 additional days.

Regards,
Precision Auto Systems`,
    timestamp: 'Yesterday, 02:20 PM',
    timeShort: '2:20 PM',
    isRead: true,
    isStarred: false,
    hasAttachment: false,
    isAiAgent: false,
    tag: 'QUANTITY LIMIT',
  },
  {
    id: 'em-8',
    folder: 'inbox',
    sender: 'Vertex Components',
    senderEmail: 'rfq@vertexcomponents.example',
    recipient: 'procurement@scops.example',
    subject: 'Expedited Delivery Option',
    snippet: 'We can support expedited delivery for the requested Brake Pad quantity. Estimated delivery: 4 days, fee: ₹12,000...',
    body: `Hello Procurement Team,

We can support expedited delivery for the requested Brake Pad quantity.

Estimated delivery: 4 days
Expedite fee: ₹12,000

Please note that the quotation is valid for 6 hours.

Regards,
Vertex Components`,
    timestamp: 'Today, 12:30 AM',
    timeShort: '12:30 AM',
    isRead: false,
    isStarred: false,
    hasAttachment: false,
    isAiAgent: false,
    tag: 'EXPEDITED OPTION',
  },
  {
    id: 'em-9',
    folder: 'inbox',
    sender: 'Metro Auto Parts',
    senderEmail: 'info@metroautoparts.example',
    recipient: 'procurement@scops.example',
    subject: 'Urgent Availability – Brake Pads',
    snippet: 'We currently have 700 Brake Pads available. Standard delivery is 6 days. Unit price: ₹128, MOQ: 300...',
    body: `Hello,

We currently have 700 Brake Pads available.

Standard delivery is 6 days.

Unit price: ₹128
Minimum order quantity: 300 units

Expedited shipping is currently unavailable.

Regards,
Metro Auto Parts`,
    timestamp: 'Yesterday, 11:15 AM',
    timeShort: '11:15 AM',
    isRead: true,
    isStarred: false,
    hasAttachment: false,
    isAiAgent: false,
    tag: 'SUPPLIER STOCK',
  },
  {
    id: 'em-10',
    folder: 'inbox',
    sender: 'Pune Vehicle Plant Procurement',
    senderEmail: 'pune-plant@company.internal',
    recipient: 'procurement@scops.example',
    subject: 'Urgent Production Requirement – Brake Pads',
    snippet: 'The Pune Vehicle Plant has confirmed that the high-priority production order requires 700 Brake Pads...',
    body: `Hello Procurement Team,

The Pune Vehicle Plant has confirmed that the current high-priority production order requires 700 Brake Pads.

Current usable inventory is expected to provide limited production coverage.

Please prioritize continuity of the high-priority order and provide an updated recovery plan.

Regards,
Pune Vehicle Plant Procurement`,
    timestamp: 'Today, 12:10 AM',
    timeShort: '12:10 AM',
    isRead: false,
    isStarred: false,
    hasAttachment: false,
    isAiAgent: false,
    tag: 'PLANT REQUIREMENT',
  },
  {
    id: 'em-11',
    folder: 'inbox',
    sender: 'DriveTech Components',
    senderEmail: 'sales@drivetech.example',
    recipient: 'procurement@scops.example',
    subject: 'Urgent RFQ Response – Brake Pads',
    snippet: 'We can supply 300 Brake Pads within 2 days. Unit price: ₹145, MOQ: 300 units, ISO 9001 certification valid...',
    body: `Hello,

We can supply 300 Brake Pads within 2 days.

Unit price: ₹145
Minimum order quantity: 300 units
Quality certification: Available (ISO 9001 / AQL 1.0)

The quantity is limited and subject to confirmation.

Regards,
DriveTech Components`,
    timestamp: 'Yesterday, 09:40 AM',
    timeShort: '9:40 AM',
    isRead: true,
    isStarred: false,
    hasAttachment: true,
    isAiAgent: false,
    tag: 'EMERGENCY QUOTE',
  },
  {
    id: 'em-12',
    folder: 'inbox',
    sender: 'Pioneer Auto Systems',
    senderEmail: 'b2b@pioneerauto.example',
    recipient: 'procurement@scops.example',
    subject: 'Emergency Supply Confirmation',
    snippet: 'We can reserve 400 Brake Pads for emergency procurement. Delivery time is approximately 5 days, unit price ₹136...',
    body: `Hello,

We can reserve 400 Brake Pads for emergency procurement.

Delivery time is approximately 5 days.

Unit price: ₹136
Quality certification: Automotive Grade

Please confirm within 6 hours if you wish to reserve this allocation.

Regards,
Pioneer Auto Systems`,
    timestamp: 'Yesterday, 08:15 AM',
    timeShort: '8:15 AM',
    isRead: true,
    isStarred: false,
    hasAttachment: false,
    isAiAgent: false,
    tag: 'CAPACITY ALLOCATION',
  },

  // 5 SENT EMAILS (4 BY AI AGENT, 1 BY HUMAN)
  {
    id: 'em-13',
    folder: 'sent',
    sender: 'Supply Chain Recovery Agent',
    senderEmail: 'ai-agent@scops.internal',
    recipient: 'Apex Auto Parts (procurement@apexautoparts.example)',
    subject: 'Urgent ETA Confirmation – PO-7712',
    snippet: 'We detected a production risk associated with the delayed delivery of PO-7712. Please confirm current shipment status...',
    body: `Hello Apex Auto Parts,

We detected a production risk associated with the delayed delivery of PO-7712.

Please confirm:
1. Current shipment status
2. Earliest achievable delivery date
3. Whether a partial shipment can be arranged
4. Quantity available for immediate dispatch

Please provide the updated information as soon as possible.

Regards,
Supply Chain Recovery Agent
AI Operations Controller`,
    timestamp: 'Today, 02:15 AM',
    timeShort: '2:15 AM',
    isRead: true,
    isStarred: true,
    hasAttachment: false,
    isAiAgent: true,
    agentRun: 'RUN-84',
    agentAction: 'Supplier Follow-up & Claim Verification',
    tag: 'AI SUPPLIER INQUIRY',
  },
  {
    id: 'em-14',
    folder: 'sent',
    sender: 'Supply Chain Recovery Agent',
    senderEmail: 'ai-agent@scops.internal',
    recipient: 'PrimeDrive Components (sales@primedrivecomponents.example)',
    subject: 'Urgent RFQ – Brake Pads',
    snippet: 'We are evaluating emergency supply options for Brake Pads. Please provide available quantity, unit price, earliest delivery...',
    body: `Hello PrimeDrive Components,

We are evaluating emergency supply options for Brake Pads.

Please provide:
- Available quantity
- Unit price
- Earliest delivery date
- Minimum order quantity
- Quality certifications
- Expedited shipping availability
- Expedited shipping cost

Please treat this as an urgent procurement request.

Regards,
Supply Chain Recovery Agent
AI Operations Controller`,
    timestamp: 'Today, 02:05 AM',
    timeShort: '2:05 AM',
    isRead: true,
    isStarred: false,
    hasAttachment: false,
    isAiAgent: true,
    agentRun: 'RUN-84',
    agentAction: 'RFQ Broadcast & Sourcing',
    tag: 'AI RFQ BROADCAST',
  },
  {
    id: 'em-15',
    folder: 'sent',
    sender: 'Supply Chain Recovery Agent',
    senderEmail: 'ai-agent@scops.internal',
    recipient: 'Vertex Components (rfq@vertexcomponents.example)',
    subject: 'Emergency RFQ – Brake Pad Supply',
    snippet: 'We require an urgent quotation for Brake Pads. Please confirm whether you can supply 600 units within 4 days...',
    body: `Hello Vertex Components,

We require an urgent quotation for Brake Pads.

Please confirm whether you can supply 600 units within 4 days.

Also provide the unit price and any expedited shipping charges.

Regards,
Supply Chain Recovery Agent
AI Operations Controller`,
    timestamp: 'Today, 02:05 AM',
    timeShort: '2:05 AM',
    isRead: true,
    isStarred: false,
    hasAttachment: false,
    isAiAgent: true,
    agentRun: 'RUN-84',
    agentAction: 'Expedited Sourcing RFQ',
    tag: 'AI RFQ BROADCAST',
  },
  {
    id: 'em-16',
    folder: 'sent',
    sender: 'Supply Chain Recovery Agent',
    senderEmail: 'ai-agent@scops.internal',
    recipient: 'DriveTech Components (sales@drivetech.example)',
    subject: 'Availability Request – Emergency Brake Pad Supply',
    snippet: 'We are evaluating a recovery plan for a high-priority production order. Please confirm available Brake Pad quantity...',
    body: `Hello DriveTech Components,

We are evaluating a recovery plan for a high-priority production order.

Please confirm your available Brake Pad quantity, earliest delivery time, unit price, MOQ, and applicable quality certifications.

If only partial quantity is available, please provide the maximum quantity that can be dispatched immediately.

Regards,
Supply Chain Recovery Agent
AI Operations Controller`,
    timestamp: 'Today, 02:04 AM',
    timeShort: '2:04 AM',
    isRead: true,
    isStarred: false,
    hasAttachment: false,
    isAiAgent: true,
    agentRun: 'RUN-84',
    agentAction: 'Split-Sourcing Feasibility Inquiry',
    tag: 'AI SOURCING INQUIRY',
  },
  {
    id: 'em-17',
    folder: 'sent',
    sender: 'Procurement Operations',
    senderEmail: 'procurement@scops.example',
    recipient: 'Apex Auto Parts (procurement@apexautoparts.example)',
    subject: 'PO-7712 – Delivery Follow-up',
    snippet: 'Please keep our procurement team updated regarding the revised delivery schedule for PO-7712...',
    body: `Hello Apex Auto Parts,

Please keep our procurement team updated regarding the revised delivery schedule for PO-7712.

We would appreciate confirmation once the shipment has been picked up by the carrier.

Regards,
Procurement Operations`,
    timestamp: 'Yesterday, 03:00 PM',
    timeShort: '3:00 PM',
    isRead: true,
    isStarred: false,
    hasAttachment: false,
    isAiAgent: false,
    tag: 'MANUAL FOLLOW-UP',
  },
];

export default function Inbox() {
  const [emails, setEmails] = useState(INITIAL_EMAILS);
  const [activeFolder, setActiveFolder] = useState('inbox'); // 'inbox' | 'starred' | 'sent'
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [checkedIds, setCheckedIds] = useState(new Set());
  const navigate = useNavigate();

  useEffect(() => {
    async function loadLiveMessages() {
      try {
        const liveMsgs = await api.getSupplierMessages();
        if (Array.isArray(liveMsgs) && liveMsgs.length > 0) {
          const formatted = liveMsgs.map((m, idx) => {
            const isOutbound = m.direction === 'outbound';
            const isDelay = m.message_text?.toLowerCase().includes('delay') || m.subject?.toLowerCase().includes('delay');
            const isClaim = m.message_text?.toLowerCase().includes('dispatched') || m.subject?.toLowerCase().includes('dispatched');

            return {
              id: `live-msg-${m.message_id || idx}`,
              folder: isOutbound ? 'sent' : 'inbox',
              sender: isOutbound
                ? 'Supply Chain Recovery Agent'
                : (m.supplier_id === 'SUP-21' ? 'Apex Auto Parts (SUP-21)' : (m.supplier_id === 'SUP-34' ? 'Metro Auto Parts (SUP-34)' : `Supplier ${m.supplier_id}`)),
              senderEmail: isOutbound ? 'ai-agent@scops.internal' : `supplier-${m.supplier_id?.toLowerCase() || 'vendor'}@scops.network`,
              recipient: isOutbound ? `${m.supplier_id} Sourcing Division` : 'procurement@scops.example',
              subject: m.subject || (isDelay ? `Delivery Delay Notification – ${m.po_id || 'PO-7712'}` : `Shipment Status Telemetry – ${m.po_id || 'PO-7712'}`),
              snippet: (m.body || m.message_text || '').slice(0, 100) + '...',
              body: m.body || m.message_text || '',
              timestamp: m.sent_at ? new Date(m.sent_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Just now',
              timeShort: m.sent_at ? new Date(m.sent_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Now',
              isRead: false,
              isStarred: true,
              hasAttachment: false,
              isAiAgent: isOutbound,
              agentRun: isOutbound ? 'AUTONOMOUS' : undefined,
              agentAction: isOutbound ? 'Automated Multi-Sourcing RFQ' : undefined,
              tag: isOutbound
                ? 'AI RFQ BROADCAST'
                : (isDelay ? 'SUPPLIER DELAY' : (isClaim ? 'SUPPLIER DISPATCH CLAIM' : 'SUPPLIER UPDATE')),
            };
          });
          setEmails((prev) => {
            const existingIds = new Set(prev.map(e => e.id));
            const newOnly = formatted.filter(f => !existingIds.has(f.id));
            return [...newOnly, ...prev];
          });
        }
      } catch {
        // Fallback gracefully to default seed emails
      }
    }
    loadLiveMessages();
  }, []);

  const toggleStar = (e, emailId) => {
    e.stopPropagation();
    setEmails((prev) =>
      prev.map((em) => (em.id === emailId ? { ...em, isStarred: !em.isStarred } : em))
    );
  };

  const toggleCheck = (e, emailId) => {
    e.stopPropagation();
    setCheckedIds((prev) => {
      const next = new Set(prev);
      if (next.has(emailId)) next.delete(emailId);
      else next.add(emailId);
      return next;
    });
  };

  const handleSelectEmail = (email) => {
    // Mark as read
    setEmails((prev) =>
      prev.map((em) => (em.id === email.id ? { ...em, isRead: true } : em))
    );
    setSelectedEmail(email);
  };

  const filteredEmails = emails.filter((em) => {
    // Folder filter
    if (activeFolder === 'inbox' && em.folder !== 'inbox') return false;
    if (activeFolder === 'sent' && em.folder !== 'sent') return false;
    if (activeFolder === 'starred' && !em.isStarred) return false;

    // Search query filter
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchSender = em.sender.toLowerCase().includes(q);
      const matchSub = em.subject.toLowerCase().includes(q);
      const matchBody = em.body.toLowerCase().includes(q);
      const matchTag = em.tag?.toLowerCase().includes(q);
      return matchSender || matchSub || matchBody || matchTag;
    }
    return true;
  });

  const unreadInboxCount = emails.filter((e) => e.folder === 'inbox' && !e.isRead).length;
  const starredCount = emails.filter((e) => e.isStarred).length;
  const sentCount = emails.filter((e) => e.folder === 'sent').length;

  return (
    <Layout>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14, height: 'calc(100vh - 80px)' }}>
        
        {/* TOP BAR / SEARCH */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: '#12161C', textTransform: 'uppercase', letterSpacing: 0.5 }}>
              Supplier Communications Matrix
            </h1>
            <p style={{ margin: '2px 0 0', fontSize: 12, color: '#8A919B' }}>
              Carrier tracking telemetry, automated RFQ dispatches & supplier confirmation logs
            </p>
          </div>

          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <div style={{ position: 'relative', width: 280 }}>
              <input
                type="text"
                placeholder="Search telemetry, supplier, PO..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  width: '100%',
                  padding: '6px 12px',
                  borderRadius: 4,
                  border: '1px solid #D5D8DC',
                  background: '#FFFFFF',
                  fontSize: 12,
                  outline: 'none',
                  fontFamily: 'var(--font-mono)',
                }}
              />
            </div>
            <Button
              onClick={() => navigate('/audit-log')}
              variant="secondary"
              style={{ fontSize: 12, padding: '6px 12px' }}
            >
              ≡ View Audit Trail
            </Button>
          </div>
        </div>

        {/* MAIN EMAIL CONTAINER */}
        <div
          style={{
            flex: 1,
            display: 'grid',
            gridTemplateColumns: '200px minmax(0, 1fr)',
            background: '#FFFFFF',
            borderRadius: 8,
            border: '1px solid #D5D8DC',
            overflow: 'hidden',
          }}
        >
          {/* FOLDER SIDEBAR */}
          <div style={{ borderRight: '1px solid #D5D8DC', background: '#F4F5F7', padding: '12px 6px', display: 'flex', flexDirection: 'column', gap: 2 }}>
            <button
              onClick={() => { setActiveFolder('inbox'); setSelectedEmail(null); }}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '8px 12px',
                borderRadius: 4,
                border: 'none',
                background: activeFolder === 'inbox' ? '#12161C' : 'transparent',
                color: activeFolder === 'inbox' ? '#FFFFFF' : '#3A4149',
                fontWeight: activeFolder === 'inbox' ? 700 : 500,
                fontSize: 12,
                cursor: 'pointer',
                textAlign: 'left',
              }}
            >
              <span>Inbox</span>
              <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)' }}>
                {emails.filter(e => e.folder === 'inbox').length}
              </span>
            </button>

            <button
              onClick={() => { setActiveFolder('starred'); setSelectedEmail(null); }}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '8px 12px',
                borderRadius: 4,
                border: 'none',
                background: activeFolder === 'starred' ? '#12161C' : 'transparent',
                color: activeFolder === 'starred' ? '#FFFFFF' : '#3A4149',
                fontWeight: activeFolder === 'starred' ? 700 : 500,
                fontSize: 12,
                cursor: 'pointer',
                textAlign: 'left',
              }}
            >
              <span>Flagged</span>
              <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)' }}>
                {starredCount}
              </span>
            </button>

            <button
              onClick={() => { setActiveFolder('sent'); setSelectedEmail(null); }}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '8px 12px',
                borderRadius: 4,
                border: 'none',
                background: activeFolder === 'sent' ? '#12161C' : 'transparent',
                color: activeFolder === 'sent' ? '#FFFFFF' : '#3A4149',
                fontWeight: activeFolder === 'sent' ? 700 : 500,
                fontSize: 12,
                cursor: 'pointer',
                textAlign: 'left',
              }}
            >
              <span>Dispatched (Agent)</span>
              <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)' }}>
                {sentCount}
              </span>
            </button>

            <div style={{ marginTop: 20, padding: '10px 8px', background: '#FFFFFF', borderRadius: 4, border: '1px solid #D5D8DC' }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: '#003DA5', marginBottom: 2, fontFamily: 'var(--font-mono)' }}>
                [AUTONOMOUS TELEMETRY]
              </div>
              <div style={{ fontSize: 11, color: '#3A4149', lineHeight: 1.3 }}>
                4 outgoing RFQs autonomously transmitted to verified vendor candidates.
              </div>
            </div>
          </div>

          {/* EMAIL LIST OR DETAIL VIEW */}
          <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflowY: 'auto' }}>
            
            {/* DETAIL VIEW */}
            {selectedEmail ? (
              <div style={{ padding: 20, display: 'flex', flexDirection: 'column', height: '100%', overflowY: 'auto' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14, borderBottom: '1px solid #D5D8DC', paddingBottom: 10 }}>
                  <button
                    onClick={() => setSelectedEmail(null)}
                    style={{
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      fontSize: 12,
                      color: '#003DA5',
                      fontWeight: 600,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 4,
                    }}
                  >
                    &larr; Back to {activeFolder === 'sent' ? 'Dispatched' : activeFolder === 'starred' ? 'Flagged' : 'Inbox'}
                  </button>

                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    {selectedEmail.tag && (
                      <span style={{ fontSize: 10, fontWeight: 700, color: '#3A4149', fontFamily: 'var(--font-mono)' }}>
                        [{selectedEmail.tag}]
                      </span>
                    )}
                  </div>
                </div>

                {/* Email Subject Header */}
                <h2 style={{ margin: '0 0 12px', fontSize: 16, fontWeight: 700, color: '#12161C' }}>
                  {selectedEmail.subject}
                </h2>

                {/* Sender Card */}
                <div
                  style={{
                    padding: 12,
                    borderRadius: 6,
                    background: '#F4F5F7',
                    border: '1px solid #D5D8DC',
                    marginBottom: 16,
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 8 }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
                        <strong style={{ fontSize: 13, color: '#12161C' }}>
                          {selectedEmail.sender}
                        </strong>
                        {selectedEmail.isAiAgent && (
                          <span style={{ fontSize: 10, color: '#003DA5', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                            [AUTONOMOUS AGENT]
                          </span>
                        )}
                      </div>
                      <div style={{ fontSize: 11, color: '#8A919B', fontFamily: 'var(--font-mono)' }}>
                        FROM: {selectedEmail.senderEmail} &bull; TO: {selectedEmail.recipient}
                      </div>
                    </div>
                    <div style={{ fontSize: 11, color: '#8A919B', fontFamily: 'var(--font-mono)' }}>
                      {selectedEmail.timestamp}
                    </div>
                  </div>

                  {selectedEmail.isAiAgent && (
                    <div style={{ marginTop: 8, paddingTop: 6, borderTop: '1px solid #D5D8DC', display: 'flex', gap: 14, fontSize: 11, color: '#003DA5', fontFamily: 'var(--font-mono)' }}>
                      <span>RUN: {selectedEmail.agentRun || 'RUN-84'}</span>
                      <span>ACTION: {selectedEmail.agentAction || 'Supplier Communication'}</span>
                    </div>
                  )}
                </div>

                {/* Email Body Content */}
                <div
                  style={{
                    fontSize: 13,
                    color: '#12161C',
                    lineHeight: 1.6,
                    whiteSpace: 'pre-line',
                    background: '#FFFFFF',
                  }}
                >
                  {selectedEmail.body}
                </div>
              </div>
            ) : (
              /* LIST VIEW */
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                {filteredEmails.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: 50, color: '#8A919B', fontFamily: 'var(--font-mono)' }}>
                    NO TRANSMISSIONS LOGGED
                  </div>
                ) : (
                  filteredEmails.map((email) => {
                    const isChecked = checkedIds.has(email.id);
                    return (
                      <div
                        key={email.id}
                        onClick={() => handleSelectEmail(email)}
                        style={{
                          display: 'grid',
                          gridTemplateColumns: '30px 20px 180px minmax(0, 1fr) 90px',
                          alignItems: 'center',
                          padding: '9px 14px',
                          borderBottom: '1px solid #D5D8DC',
                          background: email.isRead ? '#FFFFFF' : '#F4F5F7',
                          cursor: 'pointer',
                          transition: 'background 0.1s ease',
                          userSelect: 'none',
                        }}
                        onMouseEnter={(e) => (e.currentTarget.style.background = '#F4F5F7')}
                        onMouseLeave={(e) => (e.currentTarget.style.background = email.isRead ? '#FFFFFF' : '#F4F5F7')}
                      >
                        {/* Checkbox */}
                        <div onClick={(e) => toggleCheck(e, email.id)}>
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={() => {}}
                            style={{ cursor: 'pointer' }}
                          />
                        </div>

                        {/* Flag dot */}
                        <div onClick={(e) => toggleStar(e, email.id)} style={{ color: email.isStarred ? '#B98900' : '#D5D8DC', fontSize: 12 }}>
                          {email.isStarred ? '●' : '○'}
                        </div>

                        {/* Sender */}
                        <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', paddingRight: 8 }}>
                          <span
                            style={{
                              fontSize: 12,
                              fontWeight: email.isRead ? 500 : 700,
                              color: email.isAiAgent ? '#003DA5' : email.isRead ? '#3A4149' : '#12161C',
                            }}
                          >
                            {email.sender}
                          </span>
                        </div>

                        {/* Subject + Snippet preview */}
                        <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', paddingRight: 16 }}>
                          <span style={{ fontSize: 12, fontWeight: email.isRead ? 500 : 700, color: '#12161C', marginRight: 6 }}>
                            {email.subject}
                          </span>
                          <span style={{ fontSize: 12, color: '#8A919B' }}>
                            — {email.snippet}
                          </span>
                        </div>

                        {/* Timestamp */}
                        <div style={{ textAlign: 'right', fontSize: 11, fontWeight: email.isRead ? 500 : 700, color: email.isRead ? '#8A919B' : '#12161C', fontFamily: 'var(--font-mono)' }}>
                          {email.timeShort}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            )}

          </div>
        </div>

      </div>
    </Layout>
  );
}
