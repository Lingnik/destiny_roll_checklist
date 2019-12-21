import os
import json

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader

from bungie_wrapper import BungieApi
from utilities import logger


def home(request):

    oauth_url = os.environ.get('BUNGIE_OAUTH_URL')
    oauth_client_id = os.environ.get('BUNGIE_OAUTH_CLIENT_ID')
    oauth_client_secret = os.environ.get('BUNGIE_OAUTH_CLIENT_SECRET')

    request_url = oauth_url
    request_url += '?response_type=code'
    request_url += '&client_id={}'.format(oauth_client_id)
    request_url += '&state=12345'  # uh, this should be random... and persisted in the session
    request_url += '&redirect=/homepage'

    template = loader.get_template('checklist/index.html')
    context = {
        'oauth_url': request_url
    }
    return HttpResponse(template.render(context, request))

def oauth_callback(request):
    oauth_token = request.session.get('oauth_token')
    if not oauth_token:
        oauth_code = request.GET.get('code')
        bungie_client = BungieApi(os.environ.get('BUNGIE_API_TOKEN'))
        oauth_token = bungie_client.get_oauth_token(oauth_code, persist=True)
        request.session['oauth_token'] = oauth_token

    bungie_client = BungieApi(os.environ.get('BUNGIE_API_TOKEN'), oauth_token=request.session['oauth_token'])

    current_user = bungie_client.get_user_currentuser_membership()
    memberships = []
    for membership in current_user.get('destinyMemberships'):
        bungie_client.get_d2_profile(
            membership.get('membershipId'),
            membership.get('membershipType'),
            ['100']
        )
        memberships.append(membership)

    template = loader.get_template('checklist/oauth_callback.html')
    context = {
        'manifest': bungie_client.get_d2_manifest(),
        'oauth_token': json.dumps(oauth_token, indent=4),
        'current_user': json.dumps(current_user, indent=4),
        'memberships': json.dumps(memberships, indent=4),
    }
    return HttpResponse(template.render(context, request))

def bot_slash_command(request):
    """
    
    :param request: 
    :return: 
    """
    response_url = str(request.POST.get('response_url'))

    user_id = str(request.POST.get('user_id'))

    channel_id = str(request.POST.get('channel_id'))

    command = str(request.POST.get('text'))
    command = command.strip()

    print(f"<@{user_id}> ran a command in <#{channel_id}>: /hawthorne {command}")

    if command == 'help':
        template = loader.get_template('checklist/bot_slash_help.txt')
        context = {
            'response_url': response_url,
            'user_id': user_id,
            'channel_id': channel_id,
        }
        return HttpResponse(template.render(context, request))
    if command == 'unmute':
        return HttpResponse(status=500, content='Not implemented.')
    if command.startswith('mute '):
        return HttpResponse(status=500, content='Not implemented.')
    pass
