from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.forms.models import model_to_dict

from seed.bluesky.models import PropertyView, TaxLotView, TaxLotProperty
from seed.decorators import ajax_request, require_organization_id
from seed.lib.superperms.orgs.decorators import has_perm
from seed.utils.api import api_endpoint


@require_organization_id
@api_endpoint
@ajax_request
@login_required
@has_perm('requires_viewer')
def get_properties(request):
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 1)

    property_views_list = PropertyView.objects.select_related('property', 'state', 'cycle') \
        .filter(property__organization_id=request.GET['organization_id'])

    paginator = Paginator(property_views_list, per_page)

    try:
        property_views = paginator.page(page)
        page = int(page)
    except PageNotAnInteger:
        property_views = paginator.page(1)
        page = 1
    except EmptyPage:
        property_views = paginator.page(paginator.num_pages)
        page = paginator.num_pages

    response = {
        'pagination': {
            'page': page,
            'start': paginator.page(page).start_index(),
            'end': paginator.page(page).end_index(),
            'num_pages': paginator.num_pages,
            'has_next': paginator.page(page).has_next(),
            'has_previous': paginator.page(page).has_previous(),
            'total': paginator.count
        },
        'results': []
    }

    # Ids of propertyviews to look up in m2m
    prop_ids = [p.pk for p in property_views]
    joins = TaxLotProperty.objects.filter(property_view_id__in=prop_ids)

    # Get all ids of tax lots on these joins
    taxlot_view_ids = [j.taxlot_view_id for j in joins]

    # Get all tax lot views that are related
    taxlot_views = TaxLotView.objects.select_related('taxlot', 'state', 'cycle').filter(pk__in=taxlot_view_ids)

    # Map tax lot view id to tax lot view's state data
    taxlot_map = {}
    for taxlot_view in taxlot_views:
        taxlot_map[taxlot_view.pk] = model_to_dict(taxlot_view.state)

    # A mapping of property view pk to a list of taxlot state info for a taxlot view
    join_map = {}
    for join in joins:
        join_dict = {
            'primary': join.primary,
            'state': taxlot_map[join.taxlot_view_id]
        }
        try:
            join_map[join.property_view_id].append(join_dict)
        except KeyError:
            join_map[join.property_view_id] = [join_dict]

    for prop in property_views:
        p = model_to_dict(prop)
        p['state'] = model_to_dict(prop.state)
        p['property'] = model_to_dict(prop.property)
        p['cycle'] = model_to_dict(prop.cycle)
        p['related'] = join_map.get(prop.pk, [])
        response['results'].append(p)

    return response


@require_organization_id
@api_endpoint
@ajax_request
@login_required
@has_perm('requires_viewer')
def get_property(request, property_pk):
    property_view = PropertyView.objects.select_related('property', 'cycle', 'state') \
        .get(property_id=property_pk, property__organization_id=request.GET['organization_id'])

    # Lots this property is on
    lot_view_pks = TaxLotProperty.objects.filter(property_view_id=property_view.pk).values_list('taxlot_view_id', flat=True)
    lot_views = TaxLotView.objects.filter(pk__in=lot_view_pks).select_related('cycle', 'state')

    p = model_to_dict(property_view)
    p['state'] = model_to_dict(property_view.state)
    p['property'] = model_to_dict(property_view.property)
    p['cycle'] = model_to_dict(property_view.cycle)
    p['lots'] = []

    for lot in lot_views:
        p['lots'].append(model_to_dict(lot))

    return p


@require_organization_id
@api_endpoint
@ajax_request
@login_required
@has_perm('requires_viewer')
def get_taxlots(request):
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 1)

    taxlot_views_list = TaxLotView.objects.select_related('taxlot', 'state', 'cycle') \
        .filter(taxlot__organization_id=request.GET['organization_id'])

    paginator = Paginator(taxlot_views_list, per_page)

    try:
        taxlot_views = paginator.page(page)
        page = int(page)
    except PageNotAnInteger:
        taxlot_views = paginator.page(1)
        page = 1
    except EmptyPage:
        taxlot_views = paginator.page(paginator.num_pages)
        page = paginator.num_pages

    response = {
        'pagination': {
            'page': page,
            'start': paginator.page(page).start_index(),
            'end': paginator.page(page).end_index(),
            'num_pages': paginator.num_pages,
            'has_next': paginator.page(page).has_next(),
            'has_previous': paginator.page(page).has_previous(),
            'total': paginator.count
        },
        'results': []
    }

    # Ids of taxlotviews to look up in m2m
    lot_ids = [l.pk for l in taxlot_views]
    joins = TaxLotProperty.objects.filter(taxlot_view_id__in=lot_ids)

    # Get all ids of properties on these joins
    property_view_ids = [j.property_view_id for j in joins]

    # Get all property views that are related
    property_views = PropertyView.objects.select_related('property', 'state', 'cycle').filter(pk__in=property_view_ids)

    # Map property view id to property view's state data
    property_map = {}
    for property_view in property_views:
        property_map[property_view.pk] = model_to_dict(property_view.state)

    # A mapping of taxlot view pk to a list of property state info for a property view
    join_map = {}
    for join in joins:
        join_dict = {
            'primary': join.primary,
            'state': property_map[join.property_view_id]
        }
        try:
            join_map[join.taxlot_view_id].append(join_dict)
        except KeyError:
            join_map[join.taxlot_view_id] = [join_dict]

    for lot in taxlot_views:
        l = model_to_dict(lot)
        l['state'] = model_to_dict(lot.state)
        l['taxlot'] = model_to_dict(lot.taxlot)
        l['cycle'] = model_to_dict(lot.cycle)
        l['related'] = join_map.get(lot.pk, [])
        response['results'].append(l)

    return response


@require_organization_id
@api_endpoint
@ajax_request
@login_required
@has_perm('requires_viewer')
def get_taxlot(request, taxlot_pk):
    taxlot_view = TaxLotView.objects.select_related('taxlot', 'cycle', 'state') \
        .get(taxlot_id=taxlot_pk, taxlot__organization_id=request.GET['organization_id'])

    # Properties on this lot
    property_view_pks = TaxLotProperty.objects.filter(taxlot_view_id=taxlot_view.pk).values_list('property_view_id', flat=True)
    property_views = PropertyView.objects.filter(pk__in=property_view_pks).select_related('cycle', 'state')

    l = model_to_dict(taxlot_view)
    l['state'] = model_to_dict(taxlot_view.state)
    l['taxlot'] = model_to_dict(taxlot_view.taxlot)
    l['cycle'] = model_to_dict(taxlot_view.cycle)
    l['properties'] = []

    for prop in property_views:
        l['properties'].append(model_to_dict(prop))

    return l
