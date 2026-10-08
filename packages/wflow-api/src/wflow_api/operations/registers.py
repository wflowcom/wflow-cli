"""Registers: the lookup data documents refer to.

Every register GET takes the same five paging arguments and returns a paged
`{items, totalItems, pageSize, page}` envelope. The response shape is not documented
upstream; each model here is the item schema that the PUT on the same path documents.
"""

from wflow_api.client import WflowClient
from wflow_api.guards import query_params
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
