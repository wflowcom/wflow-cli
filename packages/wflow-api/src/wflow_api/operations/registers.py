"""Registers: the lookup data documents refer to.

Every register GET takes the same five paging arguments and returns a paged
`{items, totalItems, pageSize, page}` envelope. The response shape is not documented
upstream; each model here is the item schema that the PUT on the same path documents.
"""

from wflow_api.client import WflowClient
from wflow_api.guards import query_params, write_body
from wflow_api.models import (
    BusinessItemUpdateC,
    KindRegister,
    Location,
    OrganizationPerson,
    OrgSlug,
    Page,
    Paged,
    PageSize,
    PartnerFull,
    PartnerPersonUpdateC,
    PaymentMethods,
    Query,
    Register,
    Search,
    Serie,
    Sort,
    VATReturnLine,
    WriteResult,
)
from wflow_api.operation import operation


@operation
async def list_register_partners(
    client: WflowClient,
    organization: OrgSlug,
    search: Search = None,
    sort: Sort = None,
    query: Query = None,
    pageSize: PageSize = None,
    page: Page = None,
) -> Paged[PartnerFull]:
    """Business partners — the suppliers and customers documents are issued to or from.

    The register every incoming and outgoing invoice points at. Look a partner up here
    when you need its bank accounts, VAT number or payment terms rather than just the
    name printed on a document.

    Fields:

    - `name`, `ic`, `vat`, `localVAT`, `businessRegisterRegistration` — trading name, company
      registration number, VAT identification and commercial-register entry
    - `address` as one string, and `mainAddress` broken into parts
    - `customer` / `supplier` — which side of the relationship this partner is on;
      both can be true
    - `accountNo`, `bankCode`, `iban`, `bic`, `currency` — the primary bank account, flat on
      the partner; `mainAccount` and `accounts` repeat those same five names nested per account
    - `peppolIds` — Peppol e-invoicing identifiers
    - `deliveryPeriod`, `minOrderTotal`, `toleranceRate` — the terms wflow applies when
      matching invoices to orders
    - `phoneNo`, `mailAddress`, `language`, `note`
    """
    payload = (
        await client.request(
            "GET",
            f"/api/{organization}/registers/partners",
            params=query_params(search=search, sort=sort, query=query, pageSize=pageSize, page=page),
        )
        or {}
    )
    return Paged[PartnerFull].model_validate(payload)


@operation
async def list_register_accounting_rules(
    client: WflowClient,
    organization: OrgSlug,
    search: Search = None,
    sort: Sort = None,
    query: Query = None,
    pageSize: PageSize = None,
    page: Page = None,
) -> Paged[KindRegister]:
    """Accounting rules — how document lines are posted to accounts.

    Each rule belongs to one document kind, so the same code can post differently on an
    incoming invoice and on a cash receipt. Read this to explain why a document was
    posted the way it was.

    Fields:

    - `code` — the rule's identifier as used on documents
    - `description` — what it posts
    - `kind` — the document kind it applies to: IncomingInvoice, OutgoingInvoice,
      ExpenditureCashSlip, SupplierOrder, CustomerOrder, Contract, IncomeCashReceipt
      or Other
    """
    payload = (
        await client.request(
            "GET",
            f"/api/{organization}/registers/accountingrules",
            params=query_params(search=search, sort=sort, query=query, pageSize=pageSize, page=page),
        )
        or {}
    )
    return Paged[KindRegister].model_validate(payload)


@operation
async def list_register_activities(
    client: WflowClient,
    organization: OrgSlug,
    search: Search = None,
    sort: Sort = None,
    query: Query = None,
    pageSize: PageSize = None,
    page: Page = None,
) -> Paged[Register]:
    """Activities — what a cost was incurred doing, as an analytical dimension on document lines.

    One of the four dimensions a line can be tagged with: an activity says what kind
    of work the money went on, where `list_register_cost_centers` says which part of the
    organization spent it, `list_register_projects` which body of work it fed and
    `list_register_business_cases` which deal it is billed against. A single line may carry all
    four at once, so read this one only for the nature of the work.

    Fields:

    - `code` — the activity code as used on document lines
    - `description` — what the code stands for
    """
    payload = (
        await client.request(
            "GET",
            f"/api/{organization}/registers/activities",
            params=query_params(search=search, sort=sort, query=query, pageSize=pageSize, page=page),
        )
        or {}
    )
    return Paged[Register].model_validate(payload)


@operation
async def list_register_business_cases(
    client: WflowClient,
    organization: OrgSlug,
    search: Search = None,
    sort: Sort = None,
    query: Query = None,
    pageSize: PageSize = None,
    page: Page = None,
) -> Paged[Register]:
    """Business cases — the commercial engagements costs and revenues are booked against.

    A business case is the job or deal whose result is being tracked, so it gathers both the
    revenue invoiced and the costs consumed earning it. Reach for this rather than
    `list_register_projects` when the question is what a single engagement earned; a project
    follows delivery work and need not have a customer at all.

    Fields:

    - `code` — the business case code as used on document lines
    - `description` — what the code stands for
    """
    payload = (
        await client.request(
            "GET",
            f"/api/{organization}/registers/businesscases",
            params=query_params(search=search, sort=sort, query=query, pageSize=pageSize, page=page),
        )
        or {}
    )
    return Paged[Register].model_validate(payload)


@operation
async def list_register_business_item_categories(
    client: WflowClient,
    organization: OrgSlug,
    search: Search = None,
    sort: Sort = None,
    query: Query = None,
    pageSize: PageSize = None,
    page: Page = None,
) -> Paged[Register]:
    """Business item categories — the groupings the item catalogue is filed under.

    A record in `list_register_business_items` points its `category` field at one entry from
    here, so this is the vocabulary behind that field rather than something a document line
    carries itself. Read it to expand a category on an item, or to see how this workspace has
    divided its catalogue up before searching it.

    Fields:

    - `code` — the category code business items refer to
    - `description` — what the code stands for
    """
    payload = (
        await client.request(
            "GET",
            f"/api/{organization}/registers/businessitemcategories",
            params=query_params(search=search, sort=sort, query=query, pageSize=pageSize, page=page),
        )
        or {}
    )
    return Paged[Register].model_validate(payload)


@operation
async def list_register_business_items(
    client: WflowClient,
    organization: OrgSlug,
    search: Search = None,
    sort: Sort = None,
    query: Query = None,
    pageSize: PageSize = None,
    page: Page = None,
) -> Paged[BusinessItemUpdateC]:
    """Business items — the catalogue of goods and services that appear on document lines.

    Reach for this when a document line names an item and you need its list price, VAT
    rate or unit rather than just the text on the line.

    Fields:

    - `code`, `description` — the item as it appears on a line
    - `unitPrice`, `currency` — the list price and the currency it is quoted in
    - `vatType` — Exempt, FirstReduced, SecondReduced or Basic
    - `purchase` / `sales` — which side the item may be used on; both can be true
    - `measureUnit`, `category` — links into the measure unit and category registers
    - `partner` — set when the item is specific to one partner
    - `updated` — when the record last changed; sent on a read, absent from the spec's write schema
    """
    payload = (
        await client.request(
            "GET",
            f"/api/{organization}/registers/businessitems",
            params=query_params(search=search, sort=sort, query=query, pageSize=pageSize, page=page),
        )
        or {}
    )
    return Paged[BusinessItemUpdateC].model_validate(payload)


@operation
async def list_register_card_document_types(
    client: WflowClient,
    organization: OrgSlug,
    search: Search = None,
    sort: Sort = None,
    query: Query = None,
    pageSize: PageSize = None,
    page: Page = None,
) -> Paged[Register]:
    """Card document types — the types a payment made by card may be recorded as.

    Card spending is captured as its own family of documents, and this is the shortlist a card
    receipt can be filed under. It is the card counterpart of
    `list_register_cash_document_types` and the two are separate lists: a type that appears
    only there is one a card document cannot use.

    Fields:

    - `code` — the document type code as used on card documents
    - `description` — what the code stands for
    """
    payload = (
        await client.request(
            "GET",
            f"/api/{organization}/registers/carddocumenttypes",
            params=query_params(search=search, sort=sort, query=query, pageSize=pageSize, page=page),
        )
        or {}
    )
    return Paged[Register].model_validate(payload)


@operation
async def list_register_cash_document_types(
    client: WflowClient,
    organization: OrgSlug,
    search: Search = None,
    sort: Sort = None,
    query: Query = None,
    pageSize: PageSize = None,
    page: Page = None,
) -> Paged[Register]:
    """Cash document types — the types a document put through a cash register may be recorded as.

    Covers money in and money out alike, so a receipt and a payout draw on the same list. This
    names the kinds of document; `list_register_cash_registers` names the tills that produce
    them, and the two are usually needed together to read a cash document.

    Fields:

    - `code` — the document type code as used on cash documents
    - `description` — what the code stands for
    """
    payload = (
        await client.request(
            "GET",
            f"/api/{organization}/registers/cashdocumenttypes",
            params=query_params(search=search, sort=sort, query=query, pageSize=pageSize, page=page),
        )
        or {}
    )
    return Paged[Register].model_validate(payload)


@operation
async def list_register_cash_registers(
    client: WflowClient,
    organization: OrgSlug,
    search: Search = None,
    sort: Sort = None,
    query: Query = None,
    pageSize: PageSize = None,
    page: Page = None,
) -> Paged[Register]:
    """Cash registers — the tills the organization moves physical money through.

    A cash document names the register it was paid into or out of, and a workspace may keep
    several: one per site, or one per currency. Read this to learn which tills exist before
    reconciling cash, not to learn what those documents may be called.

    Fields:

    - `code` — the cash register code as used on cash documents
    - `description` — what the code stands for
    """
    payload = (
        await client.request(
            "GET",
            f"/api/{organization}/registers/cashregisters",
            params=query_params(search=search, sort=sort, query=query, pageSize=pageSize, page=page),
        )
        or {}
    )
    return Paged[Register].model_validate(payload)


@operation
async def list_register_chart_of_accounts(
    client: WflowClient,
    organization: OrgSlug,
    search: Search = None,
    sort: Sort = None,
    query: Query = None,
    pageSize: PageSize = None,
    page: Page = None,
) -> Paged[Register]:
    """Chart of accounts — the ledger accounts documents are posted to.

    This workspace's own account numbering, as mirrored from its accounting system. Use it to
    turn an account number seen on a posted line into the account's name; when the question is
    instead which account a kind of line lands on, and why, read
    `list_register_accounting_rules`.

    Fields:

    - `code` — the account number
    - `description` — the account name
    """
    payload = (
        await client.request(
            "GET",
            f"/api/{organization}/registers/chartofaccounts",
            params=query_params(search=search, sort=sort, query=query, pageSize=pageSize, page=page),
        )
        or {}
    )
    return Paged[Register].model_validate(payload)


@operation
async def list_register_contracts(
    client: WflowClient,
    organization: OrgSlug,
    search: Search = None,
    sort: Sort = None,
    query: Query = None,
    pageSize: PageSize = None,
    page: Page = None,
) -> Paged[Register]:
    """Contracts — the agreements an invoice or order can be filed under.

    Documents point here so that recurring billing can be traced back to the agreement that
    authorises it. These are lookup entries, not the contract documents themselves: expect a
    code and a name, and go to the contract's own document for its terms, dates or signatories.

    Fields:

    - `code` — the contract code documents refer to
    - `description` — what the contract covers
    """
    payload = (
        await client.request(
            "GET",
            f"/api/{organization}/registers/contracts",
            params=query_params(search=search, sort=sort, query=query, pageSize=pageSize, page=page),
        )
        or {}
    )
    return Paged[Register].model_validate(payload)


@operation
async def list_register_cost_centers(
    client: WflowClient,
    organization: OrgSlug,
    search: Search = None,
    sort: Sort = None,
    query: Query = None,
    pageSize: PageSize = None,
    page: Page = None,
) -> Paged[Register]:
    """Cost centers — the organizational units that costs are attributed to.

    An analytical dimension on document lines: a document can be split across several cost
    centers. This is the dimension that says who bore the cost — a department, a branch, a
    team — where `list_register_activities` says what was done and `list_register_projects`
    says what it was done for. Use this to resolve a code seen on a document into its meaning.

    Fields:

    - `code` — the cost center code as used on documents
    - `description` — what the code stands for
    """
    payload = (
        await client.request(
            "GET",
            f"/api/{organization}/registers/costcenters",
            params=query_params(search=search, sort=sort, query=query, pageSize=pageSize, page=page),
        )
        or {}
    )
    return Paged[Register].model_validate(payload)


@operation
async def list_register_employees(
    client: WflowClient,
    organization: OrgSlug,
    search: Search = None,
    sort: Sort = None,
    query: Query = None,
    pageSize: PageSize = None,
    page: Page = None,
) -> Paged[Register]:
    """Employees — the organization's own staff as documents name them.

    An employee is who requested a purchase, took the trip or drove the vehicle. This register
    is codes and names only; when you need contact details, or who may sign and approve in the
    organization's name, read `list_register_organization_persons` instead — the two are
    separate registers and a person can be in one without the other.

    Fields:

    - `code` — the employee code as used on documents
    - `description` — the employee's name
    """
    payload = (
        await client.request(
            "GET",
            f"/api/{organization}/registers/employees",
            params=query_params(search=search, sort=sort, query=query, pageSize=pageSize, page=page),
        )
        or {}
    )
    return Paged[Register].model_validate(payload)


@operation
async def list_register_locations(
    client: WflowClient,
    organization: OrgSlug,
    search: Search = None,
    sort: Sort = None,
    query: Query = None,
    pageSize: PageSize = None,
    page: Page = None,
) -> Paged[Location]:
    """Locations — the organization's places of business.

    A document points at a location to say where goods or services were received,
    delivered or consumed. Read this to turn a location code on a document into a street
    address, or to find who to contact at the site.

    Fields:

    - `code`, `description` — the location as it appears on a document
    - `address` — the site's address, as one string
    - `contact` — free text naming who to reach there
    """
    payload = (
        await client.request(
            "GET",
            f"/api/{organization}/registers/locations",
            params=query_params(search=search, sort=sort, query=query, pageSize=pageSize, page=page),
        )
        or {}
    )
    return Paged[Location].model_validate(payload)


@operation
async def list_register_measure_units(
    client: WflowClient,
    organization: OrgSlug,
    search: Search = None,
    sort: Sort = None,
    query: Query = None,
    pageSize: PageSize = None,
    page: Page = None,
) -> Paged[Register]:
    """Measure units — the units a quantity on a document line is counted in.

    Pieces, hours, kilograms, whatever this workspace trades in. A quantity means nothing
    without one, and an entry in `list_register_business_items` points its `measureUnit` at a
    record from here, so this is the register to read when a unit appears abbreviated on a line
    or on a catalogue item.

    Fields:

    - `code` — the unit code as used on document lines
    - `description` — what the unit is
    """
    payload = (
        await client.request(
            "GET",
            f"/api/{organization}/registers/measureunits",
            params=query_params(search=search, sort=sort, query=query, pageSize=pageSize, page=page),
        )
        or {}
    )
    return Paged[Register].model_validate(payload)


@operation
async def list_register_organization_persons(
    client: WflowClient,
    organization: OrgSlug,
    search: Search = None,
    sort: Sort = None,
    query: Query = None,
    pageSize: PageSize = None,
    page: Page = None,
) -> Paged[OrganizationPerson]:
    """Organization persons — the people on this side of a document.

    A contract or an order is signed, stamped or approved in the name of a person from
    this register. Reach for it when you need who may act for the organization on a
    document, or that person's address and contact details. These records have no `code`;
    they are identified by name.

    Fields:

    - `firstName`, `lastName` — the person's name
    - `street`, `postCode`, `city` — their address
    - `phoneNo`, `mailAddress` — how to reach them
    - `language` — ISO 639-1 code, the language to address them in
    - `contractRole` — what they may do on a contract: Sign, Stamp, Approve,
      SignWithBankId or SignWithCertificate
    """
    payload = (
        await client.request(
            "GET",
            f"/api/{organization}/registers/organizationpersons",
            params=query_params(search=search, sort=sort, query=query, pageSize=pageSize, page=page),
        )
        or {}
    )
    return Paged[OrganizationPerson].model_validate(payload)


@operation
async def list_register_partner_persons(
    client: WflowClient,
    organization: OrgSlug,
    search: Search = None,
    sort: Sort = None,
    query: Query = None,
    pageSize: PageSize = None,
    page: Page = None,
) -> Paged[PartnerPersonUpdateC]:
    """Partner persons — the contacts at partner companies.

    The counterparty side of `list_register_organization_persons`: every record names one
    partner it belongs to. Reach for it when you need the person to address at a supplier
    or customer, or who signs on their behalf. These records have no `code`; they are
    identified by name and partner.

    Fields:

    - `partner` — the partner from the partners register this person belongs to
    - `firstName`, `lastName` — the person's name
    - `street`, `postCode`, `city` — their address
    - `phoneNo`, `mailAddress` — how to reach them
    - `language` — ISO 639-1 code, the language to address them in
    - `contractRole` — what they may do on a contract: Sign, Stamp, Approve,
      SignWithBankId or SignWithCertificate
    """
    payload = (
        await client.request(
            "GET",
            f"/api/{organization}/registers/partnerpersons",
            params=query_params(search=search, sort=sort, query=query, pageSize=pageSize, page=page),
        )
        or {}
    )
    return Paged[PartnerPersonUpdateC].model_validate(payload)


@operation
async def list_register_payment_methods(
    client: WflowClient,
    organization: OrgSlug,
    search: Search = None,
    sort: Sort = None,
    query: Query = None,
    pageSize: PageSize = None,
    page: Page = None,
) -> Paged[PaymentMethods]:
    """Payment methods — how a document is settled.

    Bank transfer, card, cash and whatever else this workspace has configured. Each
    method belongs to one document kind, so what an incoming invoice may carry is not
    what a cash slip may carry.

    Fields:

    - `code`, `description` — the method as it appears on a document
    - `kind` — the document kind it applies to: IncomingInvoice, OutgoingInvoice,
      ExpenditureCashSlip, SupplierOrder, CustomerOrder, Contract, IncomeCashReceipt
      or Other
    """
    payload = (
        await client.request(
            "GET",
            f"/api/{organization}/registers/paymentmethods",
            params=query_params(search=search, sort=sort, query=query, pageSize=pageSize, page=page),
        )
        or {}
    )
    return Paged[PaymentMethods].model_validate(payload)


@operation
async def list_register_projects(
    client: WflowClient,
    organization: OrgSlug,
    search: Search = None,
    sort: Sort = None,
    query: Query = None,
    pageSize: PageSize = None,
    page: Page = None,
) -> Paged[Register]:
    """Projects — the bodies of work that costs and revenues are attributed to.

    The dimension that follows delivery: a project lasts as long as the work does and collects
    whatever is spent on it, internal work included. Choose `list_register_business_cases` when
    the subject is one deal's result, `list_register_cost_centers` when it is which unit is
    spending, and this when it is which piece of work the money went into.

    Fields:

    - `code` — the project code as used on document lines
    - `description` — what the code stands for
    """
    payload = (
        await client.request(
            "GET",
            f"/api/{organization}/registers/projects",
            params=query_params(search=search, sort=sort, query=query, pageSize=pageSize, page=page),
        )
        or {}
    )
    return Paged[Register].model_validate(payload)


@operation
async def list_register_series(
    client: WflowClient,
    organization: OrgSlug,
    search: Search = None,
    sort: Sort = None,
    query: Query = None,
    pageSize: PageSize = None,
    page: Page = None,
) -> Paged[Serie]:
    """Numbering series — the sequences documents take their numbers from.

    A series is scoped to one document kind and, on invoices, to one invoice type, so tax
    invoices and credit notes number separately. Read this to see which series a kind can
    use, or to work out which one a document number came from.

    Fields:

    - `code`, `description` — the series as it appears on a document
    - `kind` — the document kind it applies to: IncomingInvoice, OutgoingInvoice,
      ExpenditureCashSlip, SupplierOrder, CustomerOrder, Contract, IncomeCashReceipt
      or Other
    - `invoiceType` — the invoice type it numbers: TaxInvoice, CreditNote, DebitNote,
      Proforma or TaxInvoicePayment
    """
    payload = (
        await client.request(
            "GET",
            f"/api/{organization}/registers/series",
            params=query_params(search=search, sort=sort, query=query, pageSize=pageSize, page=page),
        )
        or {}
    )
    return Paged[Serie].model_validate(payload)


@operation
async def list_register_vat_control_statement_lines(
    client: WflowClient,
    organization: OrgSlug,
    search: Search = None,
    sort: Sort = None,
    query: Query = None,
    pageSize: PageSize = None,
    page: Page = None,
) -> Paged[Register]:
    """VAT control statement lines — the sections a document is itemised in on the control statement.

    The control statement is filed alongside the VAT return and reports transactions one by one
    rather than in totals, which is why a document carries a section code from here as well as a
    line code from `list_register_vat_return_lines`. Read this when the question is where a
    document will show up in the statement's detail.

    Fields:

    - `code` — the statement section code as used on documents
    - `description` — what the section covers
    """
    payload = (
        await client.request(
            "GET",
            f"/api/{organization}/registers/vatcontrolstatementlines",
            params=query_params(search=search, sort=sort, query=query, pageSize=pageSize, page=page),
        )
        or {}
    )
    return Paged[Register].model_validate(payload)


@operation
async def list_register_vat_return_lines(
    client: WflowClient,
    organization: OrgSlug,
    search: Search = None,
    sort: Sort = None,
    query: Query = None,
    pageSize: PageSize = None,
    page: Page = None,
) -> Paged[VATReturnLine]:
    """VAT return lines — the rows of the VAT return a document's tax is reported on.

    Read this to see which lines this workspace declares on, and which of them are
    reverse charge, when checking where a document's VAT ends up.

    Fields:

    - `code`, `description` — the line as it appears on a document
    - `reverseCharge` — true when the line reports tax the recipient accounts for
    """
    payload = (
        await client.request(
            "GET",
            f"/api/{organization}/registers/vatreturnlines",
            params=query_params(search=search, sort=sort, query=query, pageSize=pageSize, page=page),
        )
        or {}
    )
    return Paged[VATReturnLine].model_validate(payload)


@operation
async def list_register_vat_reverse_charge_codes(
    client: WflowClient,
    organization: OrgSlug,
    search: Search = None,
    sort: Sort = None,
    query: Query = None,
    pageSize: PageSize = None,
    page: Page = None,
) -> Paged[Register]:
    """VAT reverse charge codes — the supply codes used when the recipient accounts for the tax.

    Under the reverse charge the supplier invoices without tax and the customer declares it, and
    the law requires the kind of supply to be named by a code; this is the set of codes this
    workspace uses. It answers what makes a transaction reverse charge, where
    `list_register_vat_return_lines` answers where the resulting tax is declared.

    Fields:

    - `code` — the statutory supply code
    - `description` — the supply the code covers
    """
    payload = (
        await client.request(
            "GET",
            f"/api/{organization}/registers/vatreversechargecodes",
            params=query_params(search=search, sort=sort, query=query, pageSize=pageSize, page=page),
        )
        or {}
    )
    return Paged[Register].model_validate(payload)


@operation
async def list_register_vehicles(
    client: WflowClient,
    organization: OrgSlug,
    search: Search = None,
    sort: Sort = None,
    query: Query = None,
    pageSize: PageSize = None,
    page: Page = None,
) -> Paged[Register]:
    """Vehicles — the cars and machines that travel and fuel documents belong to.

    A fuel receipt, toll or trip report names the vehicle it was incurred on, which is what makes
    the cost attributable at all. Read this to identify a vehicle code on such a document; who
    was driving is a separate reference, into `list_register_employees`.

    Fields:

    - `code` — the vehicle code as used on documents, typically its registration
    - `description` — which vehicle it is
    """
    payload = (
        await client.request(
            "GET",
            f"/api/{organization}/registers/vehicles",
            params=query_params(search=search, sort=sort, query=query, pageSize=pageSize, page=page),
        )
        or {}
    )
    return Paged[Register].model_validate(payload)


@operation
async def update_register_partners(
    client: WflowClient, organization: OrgSlug, partners: list[PartnerFull]
) -> WriteResult:
    """Add or update whole partner records — suppliers and customers.

    A record is matched by `id`, or by `externalId` when you are reconciling against an ERP.
    Sending part of the register retires the rest: any record missing from the payload is marked
    invalid, so send every partner you mean to keep, or use `patch_register_partners`, which
    touches only the records you send. `list_register_partners` returns one page, ten records by
    default, so page through to `totalItems` before building the payload. Each submitted object
    replaces the stored record, so a field you leave out is reset to its default: send the full
    record. That includes `isValid`, which defaults to true, so a payload omitting it revives a
    record you had retired.

    `peppolIds` is the exception. Omitted, it leaves the partner's existing Peppol IDs alone; sent,
    it replaces them wholesale, so an empty list deletes every one of them.

    Bank account fields are not reliably stored: `accounts`, `mainAccount` and the flat
    `accountNo`, `bankCode`, `iban`, `bic` and `currency` can be accepted, reported as a success,
    and read back empty while the other fields in the same payload save. Do not rely on this operation
    to write account details — verify against a read before trusting a migration.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "registers/partners"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/registers/partners",
        json=write_body(partners),
    )
    return WriteResult(action="updated", resource="registers/partners")


@operation
async def update_register_accounting_rules(
    client: WflowClient, organization: OrgSlug, accountingRules: list[KindRegister]
) -> WriteResult:
    """Add or update whole accounting rule records — how document lines are posted to accounts.

    A rule is matched by `id`, or by `externalId` when reconciling against an ERP, or by `code`
    when neither is given. `kind` ties the rule to one document kind, so a code that posts
    differently on an incoming invoice and on a cash receipt is two records, not one. Sending part
    of the register retires the rest: any record missing from the payload is marked invalid, so
    send every rule you mean to keep, or use `patch_register_accounting_rules`, which touches only
    the records you send. `list_register_accounting_rules` returns one page, ten records by
    default, so page through to `totalItems` before building the payload. Each submitted object
    replaces the stored record, so a field you leave out is reset to its default — `isValid`
    included, and it defaults to true, so a payload omitting it revives a record you had retired.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "registers/accountingrules"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/registers/accountingrules",
        json=write_body(accountingRules),
    )
    return WriteResult(action="updated", resource="registers/accountingrules")


@operation
async def update_register_activities(
    client: WflowClient, organization: OrgSlug, activities: list[Register]
) -> WriteResult:
    """Add or update whole activity records — what a cost was incurred doing.

    A record is matched by `id`, or by `externalId` when reconciling against an ERP, or by `code`
    when neither is given. Sending part of the register retires the rest: any record missing from
    the payload is marked invalid, so send every record you mean to keep, or use
    `patch_register_activities`, which touches only the records you send.
    `list_register_activities` returns one page, ten records by default, so page through to
    `totalItems` before building the payload. Each submitted object replaces the stored record, so
    a field you leave out is reset to its default — `isValid` included, and it defaults to true, so
    a payload omitting it revives a record you had retired.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "registers/activities"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/registers/activities",
        json=write_body(activities),
    )
    return WriteResult(action="updated", resource="registers/activities")


@operation
async def update_register_business_cases(
    client: WflowClient, organization: OrgSlug, businessCases: list[Register]
) -> WriteResult:
    """Add or update whole business case records — the commercial engagements costs and revenues are booked against.

    A record is matched by `id`, or by `externalId` when reconciling against an ERP, or by `code`
    when neither is given. Sending part of the register retires the rest: any record missing from
    the payload is marked invalid, so send every record you mean to keep, or use
    `patch_register_business_cases`, which touches only the records you send.
    `list_register_business_cases` returns one page, ten records by default, so page through to
    `totalItems` before building the payload. Each submitted object replaces the stored record, so
    a field you leave out is reset to its default — `isValid` included, and it defaults to true, so
    a payload omitting it revives a record you had retired.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "registers/businesscases"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/registers/businesscases",
        json=write_body(businessCases),
    )
    return WriteResult(action="updated", resource="registers/businesscases")


@operation
async def update_register_business_item_categories(
    client: WflowClient, organization: OrgSlug, businessItemCategories: list[Register]
) -> WriteResult:
    """Add or update whole business item category records — the groupings the item catalogue is filed under.

    A record is matched by `id`, or by `externalId` when reconciling against an ERP, or by `code`
    when neither is given. Business items point their `category` at a record from here, so a code
    you rename here is the code those items refer to. Sending part of the register retires the
    rest: any record missing from the payload is marked invalid, so send every record you mean to
    keep, or use `patch_register_business_item_categories`, which touches only the records you
    send. `list_register_business_item_categories` returns one page, ten records by default, so
    page through to `totalItems` before building the payload. Each submitted object replaces the
    stored record, so a field you leave out is reset to its default — `isValid` included, and it
    defaults to true, so a payload omitting it revives a record you had retired.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "registers/businessitemcategories"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/registers/businessitemcategories",
        json=write_body(businessItemCategories),
    )
    return WriteResult(action="updated", resource="registers/businessitemcategories")


@operation
async def update_register_business_items(
    client: WflowClient, organization: OrgSlug, businessItems: list[BusinessItemUpdateC]
) -> WriteResult:
    """Add or update whole business item records — the catalogue of goods and services on document lines.

    An item is matched by `id`, or by `externalId` when reconciling against an ERP, or by `code`
    when neither is given. Beyond `code` and `description` it carries `unitPrice`, `currency`,
    `vatType`, whether it is for `purchase` or `sales`, and its `measureUnit`, `category` and
    `partner`, each a nested object naming that record by `id` or `externalId` — `measureUnit` and
    `category` also by `code`. Sending part of the register retires the rest: any record missing
    from the payload is marked invalid, so send every item you mean to keep, or use
    `patch_register_business_items`, which touches only the records you send.
    `list_register_business_items` returns one page, ten records by default, so page through to
    `totalItems` before building the payload. Each submitted object replaces the stored record, so
    a price or a link you leave out is reset to its default — `isValid` included, and it defaults
    to true, so a payload omitting it revives a record you had retired.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "registers/businessitems"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/registers/businessitems",
        json=write_body(businessItems),
    )
    return WriteResult(action="updated", resource="registers/businessitems")


@operation
async def update_register_card_document_types(
    client: WflowClient, organization: OrgSlug, cardDocumentTypes: list[Register]
) -> WriteResult:
    """Add or update whole card document type records — the types a payment made by card may take.

    A record is matched by `id`, or by `externalId` when reconciling against an ERP, or by `code`
    when neither is given. This list is the card side only; the cash side is a separate register,
    written through `update_register_cash_document_types`. Sending part of the register retires the
    rest: any record missing from the payload is marked invalid, so send every record you mean to
    keep, or use `patch_register_card_document_types`, which touches only the records you send.
    `list_register_card_document_types` returns one page, ten records by default, so page through
    to `totalItems` before building the payload. Each submitted object replaces the stored record,
    so a field you leave out is reset to its default — `isValid` included, and it defaults to true,
    so a payload omitting it revives a record you had retired.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "registers/carddocumenttypes"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/registers/carddocumenttypes",
        json=write_body(cardDocumentTypes),
    )
    return WriteResult(action="updated", resource="registers/carddocumenttypes")


@operation
async def update_register_cash_document_types(
    client: WflowClient, organization: OrgSlug, cashDocumentTypes: list[Register]
) -> WriteResult:
    """Add or update whole cash document type records — the types a cash register document may take.

    Covers money in and money out alike, so a receipt and a payout draw on the records written
    here. A record is matched by `id`, or by `externalId` when reconciling against an ERP, or by
    `code` when neither is given. Sending part of the register retires the rest: any record missing
    from the payload is marked invalid, so send every record you mean to keep, or use
    `patch_register_cash_document_types`, which touches only the records you send.
    `list_register_cash_document_types` returns one page, ten records by default, so page through
    to `totalItems` before building the payload. Each submitted object replaces the stored record,
    so a field you leave out is reset to its default — `isValid` included, and it defaults to true,
    so a payload omitting it revives a record you had retired.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "registers/cashdocumenttypes"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/registers/cashdocumenttypes",
        json=write_body(cashDocumentTypes),
    )
    return WriteResult(action="updated", resource="registers/cashdocumenttypes")


@operation
async def update_register_cash_registers(
    client: WflowClient, organization: OrgSlug, cashRegisters: list[Register]
) -> WriteResult:
    """Add or update whole cash register records — the tills physical money moves through.

    A record is matched by `id`, or by `externalId` when reconciling against an ERP, or by `code`
    when neither is given. These are the tills themselves, one per site or per currency; what their
    documents may be called is `update_register_cash_document_types`. Sending part of the register
    retires the rest: any record missing from the payload is marked invalid, so send every till you
    mean to keep, or use `patch_register_cash_registers`, which touches only the records you send.
    `list_register_cash_registers` returns one page, ten records by default, so page through to
    `totalItems` before building the payload. Each submitted object replaces the stored record, so
    a field you leave out is reset to its default — `isValid` included, and it defaults to true, so
    a payload omitting it revives a record you had retired.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "registers/cashregisters"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/registers/cashregisters",
        json=write_body(cashRegisters),
    )
    return WriteResult(action="updated", resource="registers/cashregisters")


@operation
async def update_register_chart_of_accounts(
    client: WflowClient, organization: OrgSlug, accounts: list[Register]
) -> WriteResult:
    """Add or update whole ledger account records — the accounts documents are posted to.

    An account is matched by `id`, or by `externalId` when reconciling against an ERP, or by `code`
    — the account number, with `description` the account name. Sending part of the register retires
    the rest: any record missing from the payload is marked invalid, so send every account you mean
    to keep, or use `patch_register_chart_of_accounts`, which touches only the records you send.
    `list_register_chart_of_accounts` returns one page, ten records by default, so page through to
    `totalItems` before building the payload. Each submitted object replaces the stored record, so
    a field you leave out is reset to its default — `isValid` included, and it defaults to true, so
    a payload omitting it revives a record you had retired.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "registers/chartofaccounts"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/registers/chartofaccounts",
        json=write_body(accounts),
    )
    return WriteResult(action="updated", resource="registers/chartofaccounts")


@operation
async def update_register_contracts(
    client: WflowClient, organization: OrgSlug, contracts: list[Register]
) -> WriteResult:
    """Add or update whole contract records — the agreements an invoice or order is filed under.

    These are lookup entries, not the contract documents themselves: a record here is the code and
    name that documents point at. It is matched by `id`, or by `externalId` when reconciling
    against an ERP, or by `code` when neither is given. Sending part of the register retires the
    rest: any record missing from the payload is marked invalid, so send every record you mean to
    keep, or use `patch_register_contracts`, which touches only the records you send.
    `list_register_contracts` returns one page, ten records by default, so page through to
    `totalItems` before building the payload. Each submitted object replaces the stored record, so
    a field you leave out is reset to its default — `isValid` included, and it defaults to true, so
    a payload omitting it revives a record you had retired.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "registers/contracts"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/registers/contracts",
        json=write_body(contracts),
    )
    return WriteResult(action="updated", resource="registers/contracts")


@operation
async def update_register_cost_centers(
    client: WflowClient, organization: OrgSlug, costCenters: list[Register]
) -> WriteResult:
    """Add or update whole cost center records — the organizational units costs are attributed to.

    A record is matched by `id`, or by `externalId` when reconciling against an ERP, or by `code`
    when neither is given. Sending part of the register retires the rest: any record missing from
    the payload is marked invalid, so send every record you mean to keep, or use
    `patch_register_cost_centers`, which touches only the records you send.
    `list_register_cost_centers` returns one page, ten records by default, so page through to
    `totalItems` before building the payload. Each submitted object replaces the stored record, so
    a field you leave out is reset to its default — `isValid` included, and it defaults to true, so
    a payload omitting it revives a record you had retired.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "registers/costcenters"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/registers/costcenters",
        json=write_body(costCenters),
    )
    return WriteResult(action="updated", resource="registers/costcenters")


@operation
async def update_register_employees(
    client: WflowClient, organization: OrgSlug, employees: list[Register]
) -> WriteResult:
    """Add or update whole employee records — the organization's own staff as documents name them.

    A record is matched by `id`, or by `externalId` when reconciling against an ERP, or by `code`
    when neither is given. This register carries codes and names only; contact details, and who may
    sign in the organization's name, belong to `update_register_organization_persons`. Sending part
    of the register retires the rest: any record missing from the payload is marked invalid, so
    send every employee you mean to keep, or use `patch_register_employees`, which touches only the
    records you send. `list_register_employees` returns one page, ten records by default, so page
    through to `totalItems` before building the payload. Each submitted object replaces the stored
    record, so a field you leave out is reset to its default — `isValid` included, and it defaults
    to true, so a payload omitting it revives a record you had retired.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "registers/employees"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/registers/employees",
        json=write_body(employees),
    )
    return WriteResult(action="updated", resource="registers/employees")


@operation
async def update_register_locations(
    client: WflowClient, organization: OrgSlug, locations: list[Location]
) -> WriteResult:
    """Add or update whole location records — the organization's places of business.

    A location is matched by `id`, or by `externalId` when reconciling against an ERP, or by `code`
    when neither is given. Beyond `code` and `description` it carries `address`, the whole site
    address as one string, and `contact`, free text naming who to reach there. Sending part of the
    register retires the rest: any record missing from the payload is marked invalid, so send every
    location you mean to keep, or use `patch_register_locations`, which touches only the records
    you send. `list_register_locations` returns one page, ten records by default, so page through
    to `totalItems` before building the payload. Each submitted object replaces the stored record,
    so an address you leave out is reset to its default — `isValid` included, and it defaults to
    true, so a payload omitting it revives a record you had retired.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "registers/locations"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/registers/locations",
        json=write_body(locations),
    )
    return WriteResult(action="updated", resource="registers/locations")


@operation
async def update_register_measure_units(
    client: WflowClient, organization: OrgSlug, measureUnits: list[Register]
) -> WriteResult:
    """Add or update whole measure unit records — the units a quantity on a line is counted in.

    A record is matched by `id`, or by `externalId` when reconciling against an ERP, or by `code`
    when neither is given. Business items point their `measureUnit` at a record from here, so a
    code you rename here is the code those items refer to. Sending part of the register retires the
    rest: any record missing from the payload is marked invalid, so send every unit you mean to
    keep, or use `patch_register_measure_units`, which touches only the records you send.
    `list_register_measure_units` returns one page, ten records by default, so page through to
    `totalItems` before building the payload. Each submitted object replaces the stored record, so
    a field you leave out is reset to its default — `isValid` included, and it defaults to true, so
    a payload omitting it revives a record you had retired.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "registers/measureunits"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/registers/measureunits",
        json=write_body(measureUnits),
    )
    return WriteResult(action="updated", resource="registers/measureunits")


@operation
async def update_register_organization_persons(
    client: WflowClient, organization: OrgSlug, persons: list[OrganizationPerson]
) -> WriteResult:
    """Add or update whole records for the people who act on the organization's behalf.

    These are the persons a contract or an order is signed, stamped or approved in the name of.
    They have no `code`: a record is matched by `id`, or by `externalId` when reconciling against
    an ERP, and carries `firstName` and `lastName`, an address, phone and mail, a `language` and
    the `contractRole` the person may take. Sending part of the register retires the rest: any
    record missing from the payload is marked invalid, so send every person you mean to keep, or
    use `patch_register_organization_persons`, which touches only the records you send.
    `list_register_organization_persons` returns one page, ten records by default, so page through
    to `totalItems` before building the payload. Each submitted object replaces the stored record,
    so a field you leave out is reset to its default — `isValid` included, and it defaults to true,
    so a payload omitting it revives a record you had retired.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "registers/organizationpersons"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/registers/organizationpersons",
        json=write_body(persons),
    )
    return WriteResult(action="updated", resource="registers/organizationpersons")


@operation
async def update_register_partner_persons(
    client: WflowClient, organization: OrgSlug, persons: list[PartnerPersonUpdateC]
) -> WriteResult:
    """Add or update whole records for the contacts at partner companies.

    The counterparty side of `update_register_organization_persons`: every record names in
    `partner` the partner it belongs to, by that partner's `id` or `externalId`. There is no `code`
    here either — a record is matched by `id`, or by `externalId` when reconciling against an ERP —
    and it carries the person's name, address, phone and mail, `language` and `contractRole`.
    Sending part of the register retires the rest, and "the register" means every contact of every
    partner, not only the partners your payload names: a call carrying one contact of partner X
    retires partner Y's contacts too. Any record missing from the payload is marked invalid, so
    send every contact you mean to keep, or use `patch_register_partner_persons`, which touches
    only the records you send. `list_register_partner_persons` returns one page, ten
    records by default, so page through to `totalItems` before building the payload. Each submitted
    object replaces the stored record, so a field you leave out is reset to its default — `isValid`
    included, and it defaults to true, so a payload omitting it revives a record you had retired.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "registers/partnerpersons"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/registers/partnerpersons",
        json=write_body(persons),
    )
    return WriteResult(action="updated", resource="registers/partnerpersons")


@operation
async def update_register_payment_methods(
    client: WflowClient, organization: OrgSlug, paymentMethods: list[PaymentMethods]
) -> WriteResult:
    """Add or update whole payment method records — how a document is settled.

    A method is matched by `id`, or by `externalId` when reconciling against an ERP, or by `code`
    when neither is given. `kind` ties the method to one document kind, so what an incoming invoice
    may carry is a different record from what a cash slip may carry. Sending part of the register
    retires the rest: any record missing from the payload is marked invalid, so send every method
    you mean to keep, or use `patch_register_payment_methods`, which touches only the records you
    send. `list_register_payment_methods` returns one page, ten records by default, so page through
    to `totalItems` before building the payload. Each submitted object replaces the stored record,
    so a field you leave out is reset to its default — `isValid` included, and it defaults to true,
    so a payload omitting it revives a record you had retired.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "registers/paymentmethods"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/registers/paymentmethods",
        json=write_body(paymentMethods),
    )
    return WriteResult(action="updated", resource="registers/paymentmethods")


@operation
async def update_register_projects(client: WflowClient, organization: OrgSlug, projects: list[Register]) -> WriteResult:
    """Add or update whole project records — the bodies of work costs and revenues are attributed to.

    A record is matched by `id`, or by `externalId` when reconciling against an ERP, or by `code`
    when neither is given. Sending part of the register retires the rest: any record missing from
    the payload is marked invalid, so send every record you mean to keep, or use
    `patch_register_projects`, which touches only the records you send. `list_register_projects`
    returns one page, ten records by default, so page through to `totalItems` before building the
    payload. Each submitted object replaces the stored record, so a field you leave out is reset to
    its default — `isValid` included, and it defaults to true, so a payload omitting it revives a
    record you had retired.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "registers/projects"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/registers/projects",
        json=write_body(projects),
    )
    return WriteResult(action="updated", resource="registers/projects")


@operation
async def update_register_series(client: WflowClient, organization: OrgSlug, series: list[Serie]) -> WriteResult:
    """Add or update whole numbering series records — the sequences documents take their numbers from.

    A series is matched by `id`, or by `externalId` when reconciling against an ERP, or by `code`
    when neither is given. `kind` scopes it to one document kind and, on invoices, `invoiceType`
    scopes it further, so tax invoices and credit notes number from separate records. Sending part
    of the register retires the rest: any record missing from the payload is marked invalid, so
    send every series you mean to keep, or use `patch_register_series`, which touches only the
    records you send. `list_register_series` returns one page, ten records by default, so page
    through to `totalItems` before building the payload. Each submitted object replaces the stored
    record, so a field you leave out is reset to its default — `isValid` included, and it defaults
    to true, so a payload omitting it revives a record you had retired.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "registers/series"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/registers/series",
        json=write_body(series),
    )
    return WriteResult(action="updated", resource="registers/series")


@operation
async def update_register_vat_control_statement_lines(
    client: WflowClient, organization: OrgSlug, lines: list[Register]
) -> WriteResult:
    """Add or update whole VAT control statement line records — the sections a document is itemised in.

    A record is matched by `id`, or by `externalId` when reconciling against an ERP, or by `code`
    when neither is given. The control statement reports transactions one by one, which is why its
    sections are a register of their own alongside `update_register_vat_return_lines`. Sending part
    of the register retires the rest: any record missing from the payload is marked invalid, so
    send every line you mean to keep, or use `patch_register_vat_control_statement_lines`, which
    touches only the records you send. `list_register_vat_control_statement_lines` returns one
    page, ten records by default, so page through to `totalItems` before building the payload. Each
    submitted object replaces the stored record, so a field you leave out is reset to its default —
    `isValid` included, and it defaults to true, so a payload omitting it revives a record you had
    retired.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "registers/vatcontrolstatementlines"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/registers/vatcontrolstatementlines",
        json=write_body(lines),
    )
    return WriteResult(action="updated", resource="registers/vatcontrolstatementlines")


@operation
async def update_register_vat_return_lines(
    client: WflowClient, organization: OrgSlug, lines: list[VATReturnLine]
) -> WriteResult:
    """Add or update whole VAT return line records — the rows a document's tax is reported on.

    A line is matched by `id`, or by `externalId` when reconciling against an ERP, or by `code`
    when neither is given, and `reverseCharge` marks the lines that report tax the recipient
    accounts for. Sending part of the register retires the rest: any record missing from the
    payload is marked invalid, so send every line you mean to keep, or use
    `patch_register_vat_return_lines`, which touches only the records you send.
    `list_register_vat_return_lines` returns one page, ten records by default, so page through to
    `totalItems` before building the payload. Each submitted object replaces the stored record, so
    a field you leave out is reset to its default — `isValid` included, and it defaults to true, so
    a payload omitting it revives a record you had retired.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "registers/vatreturnlines"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/registers/vatreturnlines",
        json=write_body(lines),
    )
    return WriteResult(action="updated", resource="registers/vatreturnlines")


@operation
async def update_register_vat_reverse_charge_codes(
    client: WflowClient, organization: OrgSlug, codes: list[Register]
) -> WriteResult:
    """Add or update whole VAT reverse charge code records — the codes naming a reverse charge supply.

    A record is matched by `id`, or by `externalId` when reconciling against an ERP, or by `code` —
    the supply code the law requires on a reverse charge document, with `description` the supply it
    covers. Sending part of the register retires the rest: any record missing from the payload is
    marked invalid, so send every code you mean to keep, or use
    `patch_register_vat_reverse_charge_codes`, which touches only the records you send.
    `list_register_vat_reverse_charge_codes` returns one page, ten records by default, so page
    through to `totalItems` before building the payload. Each submitted object replaces the stored
    record, so a field you leave out is reset to its default — `isValid` included, and it defaults
    to true, so a payload omitting it revives a record you had retired.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "registers/vatreversechargecodes"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/registers/vatreversechargecodes",
        json=write_body(codes),
    )
    return WriteResult(action="updated", resource="registers/vatreversechargecodes")


@operation
async def update_register_vehicles(client: WflowClient, organization: OrgSlug, vehicles: list[Register]) -> WriteResult:
    """Add or update whole vehicle records — the cars and machines travel and fuel documents name.

    A record is matched by `id`, or by `externalId` when reconciling against an ERP, or by `code`,
    typically the registration. Sending part of the register retires the rest: any record missing
    from the payload is marked invalid, so send every vehicle you mean to keep, or use
    `patch_register_vehicles`, which touches only the records you send. `list_register_vehicles`
    returns one page, ten records by default, so page through to `totalItems` before building the
    payload. Each submitted object replaces the stored record, so a field you leave out is reset to
    its default — `isValid` included, and it defaults to true, so a payload omitting it revives a
    record you had retired.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "registers/vehicles"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/registers/vehicles",
        json=write_body(vehicles),
    )
    return WriteResult(action="updated", resource="registers/vehicles")


@operation
async def patch_register_partners(
    client: WflowClient, organization: OrgSlug, partners: list[PartnerFull]
) -> WriteResult:
    """Add or update partner records, sparing the rest.

    Send `id` or `externalId` to identify the record, plus the record's other fields. wflow
    validates each item as a whole record, so a field you omit is reset to its default rather than
    kept — send the whole record, not just what changed. What a patch does leave alone is the
    records you keep out of the payload: they are not retired, and that is the one difference from
    `update_register_partners`. Sending a field as `null` is no different from omitting it: the
    `null` is dropped before the request leaves, and wflow ignores an explicit null in any case. To
    retire a single record, send it with `isValid: false` — and carry that field in every later
    payload for it, because `isValid` defaults to true and a write that omits it revives the
    record.

    `peppolIds` is the exception to all of that. Omitted, it leaves the partner's existing Peppol
    IDs alone; sent, it is synchronised to match your list, so an ID you did not include is deleted
    and an empty list deletes every one.

    Bank account fields are not reliably stored: `accounts`, `mainAccount` and the flat
    `accountNo`, `bankCode`, `iban`, `bic` and `currency` can be accepted, reported as a success,
    and read back empty while the other fields in the same payload save. Do not rely on this operation
    to write account details — verify against a read before trusting a migration.

    Fields: on the result —

    - `action` — "patched"
    - `resource` — "registers/partners"
    """
    await client.request(
        "PATCH",
        f"/api/{organization}/registers/partners",
        json=write_body(partners),
    )
    return WriteResult(action="patched", resource="registers/partners")


@operation
async def patch_register_accounting_rules(
    client: WflowClient, organization: OrgSlug, accountingRules: list[KindRegister]
) -> WriteResult:
    """Add or update accounting rule records, sparing the rest — how document lines are posted to accounts.

    Send `id` or `externalId` to identify the rule, or `code` when neither is given, plus the
    record's other fields. `kind` ties a rule to one document kind, so a code that posts
    differently on an incoming invoice and on a cash receipt is two records to patch, not one.
    wflow validates each item as a whole record, so a field you omit is reset to its default rather
    than kept — send the whole record, not just what changed. What a patch does leave alone is the
    rules you keep out of the payload: they are not retired, and that is the one difference from
    `update_register_accounting_rules`. Sending a field as `null` is no different from omitting it:
    the `null` is dropped before the request leaves, and wflow ignores an explicit null in any
    case. To retire a single record, send it with `isValid: false` — and carry that field in every
    later payload for it, because `isValid` defaults to true and a write that omits it revives the
    record.

    Fields: on the result —

    - `action` — "patched"
    - `resource` — "registers/accountingrules"
    """
    await client.request(
        "PATCH",
        f"/api/{organization}/registers/accountingrules",
        json=write_body(accountingRules),
    )
    return WriteResult(action="patched", resource="registers/accountingrules")


@operation
async def patch_register_activities(
    client: WflowClient, organization: OrgSlug, activities: list[Register]
) -> WriteResult:
    """Add or update activity records, sparing the rest — what a cost was incurred doing.

    Send `id` or `externalId` to identify the record, or `code` when neither is given, plus the
    record's other fields. wflow validates each item as a whole record, so a field you omit is
    reset to its default rather than kept — send the whole record, not just what changed. What a
    patch does leave alone is the records you keep out of the payload: they are not retired, and
    that is the one difference from `update_register_activities`. Sending a field as `null` is no
    different from omitting it: the `null` is dropped before the request leaves, and wflow ignores
    an explicit null in any case. To retire a single record, send it with `isValid: false` — and
    carry that field in every later payload for it, because `isValid` defaults to true and a write
    that omits it revives the record.

    Fields: on the result —

    - `action` — "patched"
    - `resource` — "registers/activities"
    """
    await client.request(
        "PATCH",
        f"/api/{organization}/registers/activities",
        json=write_body(activities),
    )
    return WriteResult(action="patched", resource="registers/activities")


@operation
async def patch_register_business_cases(
    client: WflowClient, organization: OrgSlug, businessCases: list[Register]
) -> WriteResult:
    """Add or update business cases, sparing the rest — the commercial engagements costs and revenues are booked against.

    Send `id` or `externalId` to identify the record, or `code` when neither is given, plus the
    record's other fields. wflow validates each item as a whole record, so a field you omit is
    reset to its default rather than kept — send the whole record, not just what changed. What a
    patch does leave alone is the records you keep out of the payload: they are not retired, and
    that is the one difference from `update_register_business_cases`. Sending a field as `null` is
    no different from omitting it: the `null` is dropped before the request leaves, and wflow
    ignores an explicit null in any case. To retire a single record, send it with `isValid: false`
    — and carry that field in every later payload for it, because `isValid` defaults to true and a
    write that omits it revives the record.

    Fields: on the result —

    - `action` — "patched"
    - `resource` — "registers/businesscases"
    """
    await client.request(
        "PATCH",
        f"/api/{organization}/registers/businesscases",
        json=write_body(businessCases),
    )
    return WriteResult(action="patched", resource="registers/businesscases")


@operation
async def patch_register_business_item_categories(
    client: WflowClient, organization: OrgSlug, businessItemCategories: list[Register]
) -> WriteResult:
    """Add or update business item category records, sparing the rest — the groupings the item catalogue is filed under.

    Send `id` or `externalId` to identify the record, or `code` when neither is given, plus the
    record's other fields. Business items point their `category` at a record from here, so a `code`
    you patch here is the code those items refer to. wflow validates each item as a whole record,
    so a field you omit is reset to its default rather than kept — send the whole record, not just
    what changed. What a patch does leave alone is the records you keep out of the payload: they
    are not retired, and that is the one difference from
    `update_register_business_item_categories`. Sending a field as `null` is no different from
    omitting it: the `null` is dropped before the request leaves, and wflow ignores an explicit
    null in any case. To retire a single record, send it with `isValid: false` — and carry that
    field in every later payload for it, because `isValid` defaults to true and a write that omits
    it revives the record.

    Fields: on the result —

    - `action` — "patched"
    - `resource` — "registers/businessitemcategories"
    """
    await client.request(
        "PATCH",
        f"/api/{organization}/registers/businessitemcategories",
        json=write_body(businessItemCategories),
    )
    return WriteResult(action="patched", resource="registers/businessitemcategories")


@operation
async def patch_register_business_items(
    client: WflowClient, organization: OrgSlug, businessItems: list[BusinessItemUpdateC]
) -> WriteResult:
    """Add or update business item records, sparing the rest — the catalogue of goods and services on document lines.

    Send `id` or `externalId` to identify the item, or `code` when neither is given, plus the
    record's other fields — a `unitPrice` change still has to carry the rest of the item with it.
    `category`, `measureUnit` and `partner` are nested objects naming that record by `id` or
    `externalId`, and `category` and `measureUnit` also by `code`; a nested object is replaced
    wholesale too, so re-point one by sending it complete, alongside the rest of the record. wflow
    validates each item as a whole record, so a field you omit is reset to its default rather than
    kept — send the whole record, not just what changed. What a patch does leave alone is the items
    you keep out of the payload: they are not retired, and that is the one difference from
    `update_register_business_items`. Sending a field as `null` is no different from omitting it:
    the `null` is dropped before the request leaves, and wflow ignores an explicit null in any
    case. To retire a single record, send it with `isValid: false` — and carry that field in every
    later payload for it, because `isValid` defaults to true and a write that omits it revives the
    record.

    Fields: on the result —

    - `action` — "patched"
    - `resource` — "registers/businessitems"
    """
    await client.request(
        "PATCH",
        f"/api/{organization}/registers/businessitems",
        json=write_body(businessItems),
    )
    return WriteResult(action="patched", resource="registers/businessitems")


@operation
async def patch_register_card_document_types(
    client: WflowClient, organization: OrgSlug, cardDocumentTypes: list[Register]
) -> WriteResult:
    """Add or update card document type records, sparing the rest — the types a payment made by card may take.

    Send `id` or `externalId` to identify the record, or `code` when neither is given, plus the
    record's other fields. This is the card side only; the cash side is a separate register,
    patched through `patch_register_cash_document_types`. wflow validates each item as a whole
    record, so a field you omit is reset to its default rather than kept — send the whole record,
    not just what changed. What a patch does leave alone is the records you keep out of the
    payload: they are not retired, and that is the one difference from
    `update_register_card_document_types`. Sending a field as `null` is no different from omitting
    it: the `null` is dropped before the request leaves, and wflow ignores an explicit null in any
    case. To retire a single record, send it with `isValid: false` — and carry that field in every
    later payload for it, because `isValid` defaults to true and a write that omits it revives the
    record.

    Fields: on the result —

    - `action` — "patched"
    - `resource` — "registers/carddocumenttypes"
    """
    await client.request(
        "PATCH",
        f"/api/{organization}/registers/carddocumenttypes",
        json=write_body(cardDocumentTypes),
    )
    return WriteResult(action="patched", resource="registers/carddocumenttypes")


@operation
async def patch_register_cash_document_types(
    client: WflowClient, organization: OrgSlug, cashDocumentTypes: list[Register]
) -> WriteResult:
    """Add or update cash document type records, sparing the rest — the types a cash register document may take.

    Covers money in and money out alike, so a receipt and a payout are separate records here. Send
    `id` or `externalId` to identify one, or `code` when neither is given, plus the record's other
    fields. wflow validates each item as a whole record, so a field you omit is reset to its
    default rather than kept — send the whole record, not just what changed. What a patch does
    leave alone is the records you keep out of the payload: they are not retired, and that is the
    one difference from `update_register_cash_document_types`. Sending a field as `null` is no
    different from omitting it: the `null` is dropped before the request leaves, and wflow ignores
    an explicit null in any case. To retire a single record, send it with `isValid: false` — and
    carry that field in every later payload for it, because `isValid` defaults to true and a write
    that omits it revives the record.

    Fields: on the result —

    - `action` — "patched"
    - `resource` — "registers/cashdocumenttypes"
    """
    await client.request(
        "PATCH",
        f"/api/{organization}/registers/cashdocumenttypes",
        json=write_body(cashDocumentTypes),
    )
    return WriteResult(action="patched", resource="registers/cashdocumenttypes")


@operation
async def patch_register_cash_registers(
    client: WflowClient, organization: OrgSlug, cashRegisters: list[Register]
) -> WriteResult:
    """Add or update cash register records, sparing the rest — the tills physical money moves through.

    These are the tills themselves, one per site or per currency; what their documents may be
    called is `patch_register_cash_document_types`. Send `id` or `externalId` to identify a till,
    or `code` when neither is given, plus the record's other fields. wflow validates each item as a
    whole record, so a field you omit is reset to its default rather than kept — send the whole
    record, not just what changed. What a patch does leave alone is the tills you keep out of the
    payload: they are not retired, and that is the one difference from
    `update_register_cash_registers`. Sending a field as `null` is no different from omitting it:
    the `null` is dropped before the request leaves, and wflow ignores an explicit null in any
    case. To retire a single record, send it with `isValid: false` — and carry that field in every
    later payload for it, because `isValid` defaults to true and a write that omits it revives the
    record.

    Fields: on the result —

    - `action` — "patched"
    - `resource` — "registers/cashregisters"
    """
    await client.request(
        "PATCH",
        f"/api/{organization}/registers/cashregisters",
        json=write_body(cashRegisters),
    )
    return WriteResult(action="patched", resource="registers/cashregisters")


@operation
async def patch_register_chart_of_accounts(
    client: WflowClient, organization: OrgSlug, accounts: list[Register]
) -> WriteResult:
    """Add or update ledger account records, sparing the rest — the accounts documents are posted to.

    Send `id` or `externalId` to identify the account, or `code` — the account number — when
    neither is given, plus the record's other fields; renaming an account changes `description`,
    sent with the rest. wflow validates each item as a whole record, so a field you omit is reset to its default
    rather than kept — send the whole record, not just what changed. What a patch does leave alone
    is the accounts you keep out of the payload: they are not retired, and that is the one
    difference from `update_register_chart_of_accounts`. Sending a field as `null` is no different
    from omitting it: the `null` is dropped before the request leaves, and wflow ignores an
    explicit null in any case. To retire a single record, send it with `isValid: false` — and carry
    that field in every later payload for it, because `isValid` defaults to true and a write that
    omits it revives the record.

    Fields: on the result —

    - `action` — "patched"
    - `resource` — "registers/chartofaccounts"
    """
    await client.request(
        "PATCH",
        f"/api/{organization}/registers/chartofaccounts",
        json=write_body(accounts),
    )
    return WriteResult(action="patched", resource="registers/chartofaccounts")


@operation
async def patch_register_contracts(
    client: WflowClient, organization: OrgSlug, contracts: list[Register]
) -> WriteResult:
    """Add or update contract records, sparing the rest — the agreements an invoice or order is filed under.

    These are lookup entries, not the contract documents themselves: a record here is the code and
    name that documents point at. Send `id` or `externalId` to identify one, or `code` when neither
    is given, plus the record's other fields. wflow validates each item as a whole record, so a
    field you omit is reset to its default rather than kept — send the whole record, not just what
    changed. What a patch does leave alone is the records you keep out of the payload: they are not
    retired, and that is the one difference from `update_register_contracts`. Sending a field as
    `null` is no different from omitting it: the `null` is dropped before the request leaves, and
    wflow ignores an explicit null in any case. To retire a single record, send it with `isValid:
    false` — and carry that field in every later payload for it, because `isValid` defaults to true
    and a write that omits it revives the record.

    Fields: on the result —

    - `action` — "patched"
    - `resource` — "registers/contracts"
    """
    await client.request(
        "PATCH",
        f"/api/{organization}/registers/contracts",
        json=write_body(contracts),
    )
    return WriteResult(action="patched", resource="registers/contracts")


@operation
async def patch_register_cost_centers(
    client: WflowClient, organization: OrgSlug, costCenters: list[Register]
) -> WriteResult:
    """Add or update cost center records, sparing the rest — the organizational units costs are attributed to.

    Send `id` or `externalId` to identify the record, or `code` when neither is given, plus the
    record's other fields. wflow validates each item as a whole record, so a field you omit is
    reset to its default rather than kept — send the whole record, not just what changed. What a
    patch does leave alone is the records you keep out of the payload: they are not retired, and
    that is the one difference from `update_register_cost_centers`. Sending a field as `null` is no
    different from omitting it: the `null` is dropped before the request leaves, and wflow ignores
    an explicit null in any case. To retire a single record, send it with `isValid: false` — and
    carry that field in every later payload for it, because `isValid` defaults to true and a write
    that omits it revives the record.

    Fields: on the result —

    - `action` — "patched"
    - `resource` — "registers/costcenters"
    """
    await client.request(
        "PATCH",
        f"/api/{organization}/registers/costcenters",
        json=write_body(costCenters),
    )
    return WriteResult(action="patched", resource="registers/costcenters")


@operation
async def patch_register_employees(
    client: WflowClient, organization: OrgSlug, employees: list[Register]
) -> WriteResult:
    """Add or update employee records, sparing the rest — the organization's own staff as documents name them.

    This register carries codes and names only; contact details, and who may sign in the
    organization's name, belong to `patch_register_organization_persons`. Send `id` or `externalId`
    to identify an employee, or `code` when neither is given, plus the record's other fields. wflow
    validates each item as a whole record, so a field you omit is reset to its default rather than
    kept — send the whole record, not just what changed. What a patch does leave alone is the
    employees you keep out of the payload: they are not retired, and that is the one difference
    from `update_register_employees`. Sending a field as `null` is no different from omitting it:
    the `null` is dropped before the request leaves, and wflow ignores an explicit null in any
    case. To retire a single record, send it with `isValid: false` — and carry that field in every
    later payload for it, because `isValid` defaults to true and a write that omits it revives the
    record.

    Fields: on the result —

    - `action` — "patched"
    - `resource` — "registers/employees"
    """
    await client.request(
        "PATCH",
        f"/api/{organization}/registers/employees",
        json=write_body(employees),
    )
    return WriteResult(action="patched", resource="registers/employees")


@operation
async def patch_register_locations(
    client: WflowClient, organization: OrgSlug, locations: list[Location]
) -> WriteResult:
    """Add or update location records, sparing the rest — the organization's places of business.

    Send `id` or `externalId` to identify the site, or `code` when neither is given, plus the
    record's other fields: `address` is the whole site address as one string, so a move changes that
    one field but still sends the others, and `contact` is free text naming who to reach there. wflow validates each item as a
    whole record, so a field you omit is reset to its default rather than kept — send the whole
    record, not just what changed. What a patch does leave alone is the sites you keep out of the
    payload: they are not retired, and that is the one difference from `update_register_locations`.
    Sending a field as `null` is no different from omitting it: the `null` is dropped before the
    request leaves, and wflow ignores an explicit null in any case. To retire a single record, send
    it with `isValid: false` — and carry that field in every later payload for it, because
    `isValid` defaults to true and a write that omits it revives the record.

    Fields: on the result —

    - `action` — "patched"
    - `resource` — "registers/locations"
    """
    await client.request(
        "PATCH",
        f"/api/{organization}/registers/locations",
        json=write_body(locations),
    )
    return WriteResult(action="patched", resource="registers/locations")


@operation
async def patch_register_measure_units(
    client: WflowClient, organization: OrgSlug, measureUnits: list[Register]
) -> WriteResult:
    """Add or update measure unit records, sparing the rest — the units a quantity on a line is counted in.

    Send `id` or `externalId` to identify the unit, or `code` when neither is given, plus the
    record's other fields. Business items point their `measureUnit` at a record from here, so a
    `code` you patch here is the code those items refer to. wflow validates each item as a whole
    record, so a field you omit is reset to its default rather than kept — send the whole record,
    not just what changed. What a patch does leave alone is the units you keep out of the payload:
    they are not retired, and that is the one difference from `update_register_measure_units`.
    Sending a field as `null` is no different from omitting it: the `null` is dropped before the
    request leaves, and wflow ignores an explicit null in any case. To retire a single record, send
    it with `isValid: false` — and carry that field in every later payload for it, because
    `isValid` defaults to true and a write that omits it revives the record.

    Fields: on the result —

    - `action` — "patched"
    - `resource` — "registers/measureunits"
    """
    await client.request(
        "PATCH",
        f"/api/{organization}/registers/measureunits",
        json=write_body(measureUnits),
    )
    return WriteResult(action="patched", resource="registers/measureunits")


@operation
async def patch_register_organization_persons(
    client: WflowClient, organization: OrgSlug, persons: list[OrganizationPerson]
) -> WriteResult:
    """Add or update records, sparing the rest, for the people who act on the organization's behalf.

    These are the persons a contract or an order is signed, stamped or approved in the name of.
    They have no `code`: send `id` or `externalId` to identify one, plus the record's other fields
    — a new `phoneNo`, `mailAddress` or `contractRole` travels with the rest of them. wflow validates each
    item as a whole record, so a field you omit is reset to its default rather than kept — send the
    whole record, not just what changed. What a patch does leave alone is the people you keep out
    of the payload: they are not retired, and that is the one difference from
    `update_register_organization_persons`. Sending a field as `null` is no different from omitting
    it: the `null` is dropped before the request leaves, and wflow ignores an explicit null in any
    case. To retire a single record, send it with `isValid: false` — and carry that field in every
    later payload for it, because `isValid` defaults to true and a write that omits it revives the
    record.

    Fields: on the result —

    - `action` — "patched"
    - `resource` — "registers/organizationpersons"
    """
    await client.request(
        "PATCH",
        f"/api/{organization}/registers/organizationpersons",
        json=write_body(persons),
    )
    return WriteResult(action="patched", resource="registers/organizationpersons")


@operation
async def patch_register_partner_persons(
    client: WflowClient, organization: OrgSlug, persons: list[PartnerPersonUpdateC]
) -> WriteResult:
    """Add or update records, sparing the rest, for the contacts at partner companies.

    The counterparty side of `patch_register_organization_persons`. There is no `code` here either:
    send `id` or `externalId` to identify the contact, plus the record's other fields — a name, an
    address, `phoneNo`, `mailAddress`, `language` or `contractRole`. `partner` names the partner
    the contact belongs to, by that partner's `id` or `externalId`. Send it on every call, not only
    when moving a contact: a payload omitting it is rejected. wflow validates each item as a
    whole record,
    so a field you omit is reset to its default rather than kept — send the whole record, not just
    what changed. What a patch does leave alone is the contacts you keep out of the payload: they
    are not retired, and that is the one difference from `update_register_partner_persons`. Sending
    a field as `null` is no different from omitting it: the `null` is dropped before the request
    leaves, and wflow ignores an explicit null in any case. To retire a single record, send it with
    `isValid: false` — and carry that field in every later payload for it, because `isValid`
    defaults to true and a write that omits it revives the record.

    Fields: on the result —

    - `action` — "patched"
    - `resource` — "registers/partnerpersons"
    """
    await client.request(
        "PATCH",
        f"/api/{organization}/registers/partnerpersons",
        json=write_body(persons),
    )
    return WriteResult(action="patched", resource="registers/partnerpersons")


@operation
async def patch_register_payment_methods(
    client: WflowClient, organization: OrgSlug, paymentMethods: list[PaymentMethods]
) -> WriteResult:
    """Add or update payment method records, sparing the rest — how a document is settled.

    Send `id` or `externalId` to identify the method, or `code` when neither is given, plus the
    record's other fields. `kind` ties a method to one document kind, so what an incoming invoice
    may carry is a separate record from what a cash slip may carry, and each is patched on its own.
    wflow validates each item as a whole record, so a field you omit is reset to its default rather
    than kept — send the whole record, not just what changed. What a patch does leave alone is the
    methods you keep out of the payload: they are not retired, and that is the one difference from
    `update_register_payment_methods`. Sending a field as `null` is no different from omitting it:
    the `null` is dropped before the request leaves, and wflow ignores an explicit null in any
    case. To retire a single record, send it with `isValid: false` — and carry that field in every
    later payload for it, because `isValid` defaults to true and a write that omits it revives the
    record.

    Fields: on the result —

    - `action` — "patched"
    - `resource` — "registers/paymentmethods"
    """
    await client.request(
        "PATCH",
        f"/api/{organization}/registers/paymentmethods",
        json=write_body(paymentMethods),
    )
    return WriteResult(action="patched", resource="registers/paymentmethods")


@operation
async def patch_register_projects(client: WflowClient, organization: OrgSlug, projects: list[Register]) -> WriteResult:
    """Add or update project records, sparing the rest — the bodies of work costs and revenues are attributed to.

    Send `id` or `externalId` to identify the record, or `code` when neither is given, plus the
    record's other fields. wflow validates each item as a whole record, so a field you omit is
    reset to its default rather than kept — send the whole record, not just what changed. What a
    patch does leave alone is the records you keep out of the payload: they are not retired, and
    that is the one difference from `update_register_projects`. Sending a field as `null` is no
    different from omitting it: the `null` is dropped before the request leaves, and wflow ignores
    an explicit null in any case. To retire a single record, send it with `isValid: false` — and
    carry that field in every later payload for it, because `isValid` defaults to true and a write
    that omits it revives the record.

    Fields: on the result —

    - `action` — "patched"
    - `resource` — "registers/projects"
    """
    await client.request(
        "PATCH",
        f"/api/{organization}/registers/projects",
        json=write_body(projects),
    )
    return WriteResult(action="patched", resource="registers/projects")


@operation
async def patch_register_series(client: WflowClient, organization: OrgSlug, series: list[Serie]) -> WriteResult:
    """Add or update numbering series records, sparing the rest — the sequences documents take their numbers from.

    Send `id` or `externalId` to identify the series, or `code` when neither is given, plus the
    record's other fields. `kind` scopes a series to one document kind and, on invoices,
    `invoiceType` scopes it further, so tax invoices and credit notes are separate records to
    patch. wflow validates each item as a whole record, so a field you omit is reset to its default
    rather than kept — send the whole record, not just what changed. What a patch does leave alone
    is the series you keep out of the payload: they are not retired, and that is the one difference
    from `update_register_series`. Sending a field as `null` is no different from omitting it: the
    `null` is dropped before the request leaves, and wflow ignores an explicit null in any case. To
    retire a single record, send it with `isValid: false` — and carry that field in every later
    payload for it, because `isValid` defaults to true and a write that omits it revives the
    record.

    Fields: on the result —

    - `action` — "patched"
    - `resource` — "registers/series"
    """
    await client.request(
        "PATCH",
        f"/api/{organization}/registers/series",
        json=write_body(series),
    )
    return WriteResult(action="patched", resource="registers/series")


@operation
async def patch_register_vat_control_statement_lines(
    client: WflowClient, organization: OrgSlug, lines: list[Register]
) -> WriteResult:
    """Add or update VAT control statement line records, sparing the rest — the sections a document is itemised in.

    The control statement reports transactions one by one, which is why its sections are a register
    of their own alongside `patch_register_vat_return_lines`. Send `id` or `externalId` to identify
    a section, or `code` when neither is given, plus the record's other fields. wflow validates
    each item as a whole record, so a field you omit is reset to its default rather than kept —
    send the whole record, not just what changed. What a patch does leave alone is the sections you
    keep out of the payload: they are not retired, and that is the one difference from
    `update_register_vat_control_statement_lines`. Sending a field as `null` is no different from
    omitting it: the `null` is dropped before the request leaves, and wflow ignores an explicit
    null in any case. To retire a single record, send it with `isValid: false` — and carry that
    field in every later payload for it, because `isValid` defaults to true and a write that omits
    it revives the record.

    Fields: on the result —

    - `action` — "patched"
    - `resource` — "registers/vatcontrolstatementlines"
    """
    await client.request(
        "PATCH",
        f"/api/{organization}/registers/vatcontrolstatementlines",
        json=write_body(lines),
    )
    return WriteResult(action="patched", resource="registers/vatcontrolstatementlines")


@operation
async def patch_register_vat_return_lines(
    client: WflowClient, organization: OrgSlug, lines: list[VATReturnLine]
) -> WriteResult:
    """Add or update VAT return line records, sparing the rest — the rows a document's tax is reported on.

    Send `id` or `externalId` to identify the line, or `code` when neither is given, plus the
    record's other fields; `reverseCharge` marks the lines that report tax the recipient accounts
    for, and sending it `false` is a change, not a clearing. wflow validates each item as a whole
    record, so a field you omit is reset to its default rather than kept — send the whole record,
    not just what changed. What a patch does leave alone is the lines you keep out of the payload:
    they are not retired, and that is the one difference from `update_register_vat_return_lines`.
    Sending a field as `null` is no different from omitting it: the `null` is dropped before the
    request leaves, and wflow ignores an explicit null in any case. To retire a single record, send
    it with `isValid: false` — and carry that field in every later payload for it, because
    `isValid` defaults to true and a write that omits it revives the record.

    Fields: on the result —

    - `action` — "patched"
    - `resource` — "registers/vatreturnlines"
    """
    await client.request(
        "PATCH",
        f"/api/{organization}/registers/vatreturnlines",
        json=write_body(lines),
    )
    return WriteResult(action="patched", resource="registers/vatreturnlines")


@operation
async def patch_register_vat_reverse_charge_codes(
    client: WflowClient, organization: OrgSlug, codes: list[Register]
) -> WriteResult:
    """Add or update VAT reverse charge code records, sparing the rest — the codes naming a reverse charge supply.

    Send `id` or `externalId` to identify the record, or `code` — the supply code the law requires
    on a reverse charge document — when neither is given, plus the record's other fields; restating
    the supply changes `description`, sent with the rest. wflow validates each item as a whole record, so a field
    you omit is reset to its default rather than kept — send the whole record, not just what
    changed. What a patch does leave alone is the codes you keep out of the payload: they are not
    retired, and that is the one difference from `update_register_vat_reverse_charge_codes`.
    Sending a field as `null` is no different from omitting it: the `null` is dropped before the
    request leaves, and wflow ignores an explicit null in any case. To retire a single record, send
    it with `isValid: false` — and carry that field in every later payload for it, because
    `isValid` defaults to true and a write that omits it revives the record.

    Fields: on the result —

    - `action` — "patched"
    - `resource` — "registers/vatreversechargecodes"
    """
    await client.request(
        "PATCH",
        f"/api/{organization}/registers/vatreversechargecodes",
        json=write_body(codes),
    )
    return WriteResult(action="patched", resource="registers/vatreversechargecodes")


@operation
async def patch_register_vehicles(client: WflowClient, organization: OrgSlug, vehicles: list[Register]) -> WriteResult:
    """Add or update vehicle records, sparing the rest — the cars and machines travel and fuel documents name.

    Send `id` or `externalId` to identify the vehicle, or `code` — typically the registration —
    when neither is given, plus the record's other fields. wflow validates each item as a whole
    record, so a field you omit is reset to its default rather than kept — send the whole record,
    not just what changed. What a patch does leave alone is the vehicles you keep out of the
    payload: they are not retired, and that is the one difference from `update_register_vehicles`.
    Sending a field as `null` is no different from omitting it: the `null` is dropped before the
    request leaves, and wflow ignores an explicit null in any case. To retire a single record, send
    it with `isValid: false` — and carry that field in every later payload for it, because
    `isValid` defaults to true and a write that omits it revives the record.

    Fields: on the result —

    - `action` — "patched"
    - `resource` — "registers/vehicles"
    """
    await client.request(
        "PATCH",
        f"/api/{organization}/registers/vehicles",
        json=write_body(vehicles),
    )
    return WriteResult(action="patched", resource="registers/vehicles")
