from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.template.defaultfilters import register
from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from rest_framework.response import Response

from hackernews.models import Comment, Contribution, UserDetail, SubmitForm, ContributionVote, CommentVote, DetailForm, \
    UserDTO, ContributionDTO, CommentDTO
from hackernews.serializers import UserDTOSerializer, ContributionDTOSerializer, ContributionCreationDTOSerializer, \
    CommentDTOSerializer, CommentCreationDTOSerializer


def vote(request):
    if request.user.is_authenticated:
        id = request.POST.get('id')
        contribution = Contribution.objects.get(id=id)
        contribution.points = contribution.points + 1
        contribution.save()
        contributionvote = ContributionVote()
        contributionvote.user = request.user
        contributionvote.contribution = contribution
        contributionvote.save()
    else:
        return redirect('/login')
    return redirect(request.POST.get('next'))


def unvote(request, id):
    if request.user.is_authenticated:
        contribution = Contribution.objects.get(id=id)
        contribution.points = contribution.points - 1
        contribution.save()
        ContributionVote.objects.get(user=request.user, contribution=contribution).delete()
    else:
        return redirect('/login')
    return redirect(request.GET.get('next'))


def votecomment(request):
    if request.user.is_authenticated:
        id = request.POST.get('id')
        comment = Comment.objects.get(id=id)
        comment.votes = comment.votes + 1
        comment.save()
        commentvote = CommentVote()
        commentvote.user = request.user
        commentvote.comment = comment
        commentvote.save()
    else:
        return redirect('/login')
    return redirect(request.POST.get('next'))


def unvotecomment(request, id):
    if request.user.is_authenticated:
        comment = Comment.objects.get(id=id)
        comment.votes = comment.votes - 1
        comment.save()
        CommentVote.objects.get(user=request.user, comment=comment).delete()
    else:
        return redirect('/login')
    return redirect(request.GET.get('next'))


def index(request):
    votes = None
    karma = 0
    if request.user.is_authenticated:
        votes = ContributionVote.objects.filter(user=request.user).values_list('contribution', flat=True)
        karma = UserDetail.objects.get(user=request.user).karma
    return render(request, "news.html", {
        "contributions": Contribution.objects.all().order_by('-points'),
        "submit": False,
        "votes": votes,
        "karma": karma,
        "bottom": True
    })


def newest(request):
    votes = None
    if request.user.is_authenticated:
        votes = ContributionVote.objects.filter(user=request.user)
    return render(request, "news.html", {
        "contributions": Contribution.objects.all().order_by('-date'),
        "submit": False,
        "selected": "newest",
        "votes": votes,
        "bottom": True,
        "karma": get_karma(request)
    })


def threads(request):
    author = User.objects.get(username=request.GET.get('id'))
    fathers = Comment.objects.filter(author=author).order_by('level', '-date')
    comments = []

    for com in fathers:
        if not_in(com, comments):
            comments.append(com)
            orderCommments(com.level + 1, com, comments)

    fix_order(comments)

    votedcomments = None
    if request.user.is_authenticated:
        votedcomments = CommentVote.objects.filter(user=request.user)

    return render(request, "commenttree.html", {
        "comments": comments,
        "votedcomments": votedcomments,
        "selected": "threads",
        "karma": get_karma(request),
        "bottom": True,
        "actualuser": request.GET.get('id')
    })


def fix_order(comments):
    i = 0
    if len(comments) > 0:
        ant = comments[0]
        for c in comments:
            if c != ant and c.father != ant:
                c.level = 0
                i = 0
            else:
                c.level = i

            if ant != c.father:
                ant = c
                i = i + 1


def not_in(com, comments):
    for c in comments:
        if (c.id == com.id):
            return False

    return True


def ask(request):
    votes = None
    if request.user.is_authenticated:
        votes = ContributionVote.objects.filter(user=request.user).values_list('contribution', flat=True)
    return render(request, "news.html", {
        "contributions": Contribution.objects.filter(type="ask").order_by('-points'),
        "submit": False,
        "selected": "ask",
        "votes": votes,
        "bottom": True,
        "karma": get_karma(request)
    })


def profile(request):
    username = request.GET.get('id')
    user = User.objects.get(username=username)
    userDetail = UserDetail.objects.get(user=user)
    key = Token.objects.get(user=user).key

    if request.method == 'POST':
        if request.user.is_authenticated:
            form = DetailForm(request.POST)
            if form.is_valid():
                userDetail.set_data(form)
                userDetail.save()

    karma = get_karma(request)

    form = DetailForm(
        initial={'about': userDetail.about, 'show_dead': userDetail.show_dead, 'no_procrast': userDetail.no_procrast,
                 'max_visit': userDetail.max_visit, 'min_away': userDetail.min_away, 'delay': userDetail.delay})

    return render(request, "profile.html", {
        "profile": user,
        "profileDetails": userDetail,
        "submit": False,
        "karma": karma,
        "form": form,
        "bottom": False,
        "key": key
    })


comments = []
fathers = []


def item(request, id):
    if request.method == 'POST':
        if request.user.is_authenticated:
            comment = Comment()
            comment.contribution = Contribution.objects.get(id=request.POST.get('contribution'))
            comment.text = request.POST.get('text')
            comment.author = request.user
            level = request.POST.get('level')
            comment.level = level
            if level != 0:
                comment.father = request.POST.get('father')
            comment.save()
            return redirect('/item/' + str(request.POST.get('contribution')))
        else:
            return redirect('/login')

    fathers = Comment.objects.filter(contribution=Contribution.objects.get(id=id)).filter(level=0).order_by('-votes')
    comments = []

    for com in fathers:
        comments.append(com)
        orderComments(1, com, comments, id)

    voted = None
    votedcomments = None
    if request.user.is_authenticated:
        voted = ContributionVote.objects.filter(user=request.user,
                                                contribution=Contribution.objects.get(id=id)).exists()
        votedcomments = CommentVote.objects.filter(user=request.user)

    karma = get_karma(request)

    return render(request, "comment.html", {
        "contribution": Contribution.objects.get(id=id),
        "comments": comments,
        "voted": voted,
        "votedcomments": votedcomments,
        "karma": karma,
        "bottom": True
    })


def orderComments(i, father, comments, id):
    children = Comment.objects.filter(contribution=Contribution.objects.get(id=id)).filter(level=i).filter(
        father=father)
    for child in children:
        gchildren = Comment.objects.filter(contribution=Contribution.objects.get(id=id)).filter(level=i + 1).filter(
            father=child)

        if len(gchildren) == 0:
            comments.append(child)
        else:
            comments.append(child)
            orderComments(i + 1, child, comments, id)


def orderCommments(i, father, comments):
    children = Comment.objects.filter(level=i).filter(father=father)
    for child in children:
        comments.append(child)


def reply(request, id):
    if not request.user.is_authenticated:
        return redirect('/login')

    if request.method == 'POST':
        if len(request.POST.get('text')) == 0:
            return errormessage(request)
        father = Comment.objects.get(id=request.POST.get('father'))
        comment = Comment()
        comment.text = request.POST.get('text')
        comment.father = father
        comment.level = father.level + 1
        comment.contribution = father.contribution
        comment.author = request.user
        comment.save()
        return redirect('/item/' + str(father.contribution.id))

    return render(request, "reply.html", {
        "comment": Comment.objects.get(id=id),
        "voted": CommentVote.objects.filter(user=request.user, comment=Comment.objects.get(id=id)).exists(),
        "bottom": False,
        "submit": False,
        "reply": True
    })


class SubmitView(TemplateView):
    template_name = "submit.html"

    def get(self, request):
        form = SubmitForm
        if request.user.is_authenticated:
            return render(request, self.template_name, {"form": form, "submit": True})
        return redirect('/login')

    def post(self, request):
        form = SubmitForm(request.POST)
        url = request.POST.get('url')
        if form.is_valid():
            c = Contribution()
            c.title = request.POST.get('title')
            c.url = request.POST.get('url')
            c.author = request.user
            if not c.url:
                c.text = request.POST.get('text')
                c.type = 'ask'
            else:
                match = Contribution.objects.filter(url=url).exists()
                if match:
                    return redirect('../item/' + str(Contribution.objects.get(url=url).id))
            c.save()
            if request.POST.get('url') and request.POST.get('text'):
                com = Comment()
                com.author = request.user
                com.text = request.POST.get('text')
                com.contribution = Contribution.objects.get(url=c.url)
                com.save()
            ud = UserDetail.objects.get(user=request.user)
            ud.karma = ud.karma + 1
            ud.save()
            return redirect('/newest')
        return errormessage(request)


def errormessage(request):
    return render(request, "message.html")


def signout(request):
    logout(request)
    return redirect('/')


class LoginView(TemplateView):
    template_name = 'login.html'

    def get(self, request, *args, **kwargs):

        creationForm = UserCreationForm(prefix='creation')
        creationForm.fields['username'].required = False
        creationForm.fields['password1'].required = False
        creationForm.fields['password2'].required = False
        loginForm = AuthenticationForm(prefix='login')
        loginForm.fields['username'].required = False
        loginForm.fields['password'].required = False

        return self.render_to_response(
            {'c_form': creationForm, 'a_form': loginForm})

    def post(self, request, *args, **kwargs):
        creationForm = UserCreationForm(request.POST, prefix='creation')
        form = AuthenticationForm(request.POST, prefix='login')
        if 'creation' in request.POST and creationForm.is_bound and creationForm.is_valid():
            creationForm.save()
            user = creationForm.cleaned_data['username']
            password = creationForm.cleaned_data['password1']
            user = authenticate(request, username=user, password=password)
            login(request, user)
            return redirect('/')
        elif 'login' in request.POST:
            username = request.POST['login-username']
            password = request.POST['login-password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('/')

        return self.render_to_response({'c_form': creationForm, 'a_form': AuthenticationForm(prefix='login')})


def createuser(request):
    if not UserDetail.objects.filter(user=request.user).exists():
        userDetails = UserDetail(user=request.user)
        Token.objects.create(user=request.user)
        userDetails.save()

    return redirect('/')


@register.filter
def in_category(things, contribution):
    return things.filter(contribution=contribution)


@register.filter
def in_category2(things, comment):
    return things.filter(comment=comment)


def submission(request):
    karma = get_karma(request)
    votes = None
    if request.user.is_authenticated:
        votes = ContributionVote.objects.filter(user=request.user)
    contributions = Contribution.objects.filter(author=User.objects.get(username=request.GET.get('id'))).order_by(
        '-date')
    return render(request, "news.html", {
        "contributions": contributions,
        "submit": False,
        "selected": "",
        "votes": votes,
        "karma": karma,
        "actualuser": request.GET.get('id')
    })


def favourites(request):
    votes = None
    if request.user.is_authenticated:
        votes = ContributionVote.objects.filter(user=request.user)

    contributions = []
    votedcontributions = ContributionVote.objects.filter(user=User.objects.get(username=request.GET.get('id')))
    for c in votedcontributions:
        contributions.append(c.contribution)

    return render(request, "news.html", {
        "contributions": contributions,
        "submit": False,
        "selected": "",
        "votes": votes,
        "karma": get_karma(request),
        "actualuser": request.user
    })


def favcomments(request):
    votes = None
    if request.user.is_authenticated:
        votes = CommentVote.objects.filter(user=request.user)

    coments = []
    votedcomments = CommentVote.objects.filter(user=User.objects.get(username=request.GET.get('id')))
    for c in votedcomments:
        coments.append(c.comment)

    fix_order(coments)

    return render(request, "commenttree.html", {
        "comments": coments,
        "submit": False,
        "selected": "",
        "votedcomments": votes,
        "karma": get_karma(request),
        "actualuser": request.user
    })


def get_karma(request):
    if request.user.is_authenticated:
        return UserDetail.objects.get(user=request.user).karma

    return None


# API

@api_view(['GET', 'POST'])
def comments_id_api(request, id):

    token = request.META.get('HTTP_AUTHORIZATION')

    if token is None:
        return Response({
            "authentication": ["This field is required."]
        }, status=status.HTTP_401_UNAUTHORIZED)

    try:
        auth = Token.objects.get(key=token)
    except Token.DoesNotExist:
        return Response({
            "authentication": ["This key is invalid."]
        }, status=status.HTTP_401_UNAUTHORIZED)

    if request.method == 'GET':
        try:
            c = Comment.objects.get(id=id)
            if c.father is None:
                f = None
            else:
                f = c.father.id

            comment_dto = CommentDTO(c.id, c.level, c.author, c.text, c.votes, c.date, c.contribution.id, f)
            serializer = CommentDTOSerializer(comment_dto)
            return Response(serializer.data)

    except Comment.DoesNotExist:
        return Response({
            "id": ["This id is not found."]
        }, status=status.HTTP_404_NOT_FOUND)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = CommentCreationDTOSerializer(data=data)
        if serializer.is_valid():
            father = Comment.objects.get(id=id)
            comment = Comment()
            comment.text = serializer.data.get('text')
            comment.father = father
            comment.level = father.level + 1
            comment.contribution = father.contribution
            comment.author = auth.user
            comment.save()

            serializer = CommentDTOSerializer(comment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
def submissions_id_api(request, id):
    token = request.META.get('HTTP_AUTHORIZATION')

    if token is None:
        return Response({
            "authentication": ["This field is required."]
        }, status=status.HTTP_401_UNAUTHORIZED)

    try:
        auth = Token.objects.get(key=token)
    except Token.DoesNotExist:
        return Response({
            "authentication": ["This key is invalid."]
        }, status=status.HTTP_401_UNAUTHORIZED)

    try:
        # TODO falta els comments
        c = Contribution.objects.get(id=id)
        contribution_dto = ContributionDTO(c.id, c.title, c.type, c.points, c.author.username, c.url, c.text, c.date)
        serializer = ContributionDTOSerializer(contribution_dto)
        return Response(serializer.data)

    except Contribution.DoesNotExist:
        return Response({
            "id": ["This id is not found."]
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET', 'POST'])
def submissions_api(request):
    token = request.META.get('HTTP_AUTHORIZATION')
    # TODO falta els coments
    if token is None:
        return Response({
            "authentication": ["This field is required."]
        }, status=status.HTTP_401_UNAUTHORIZED)

    try:
        auth = Token.objects.get(key=token)
    except Token.DoesNotExist:
        return Response({
            "authentication": ["This key is invalid."]
        }, status=status.HTTP_401_UNAUTHORIZED)

    if request.method == 'GET':
        id = request.GET.get("id", None)
        filter = request.GET.get("filter", None)
        type = request.GET.get("type", None)

        #obtenir les submissions d'un usuari concret
        if id is not None and filter is None and type is None:

            contributions = Contribution.objects.filter(
                author=User.objects.get(username=request.GET.get('id'))).order_by(
                '-date')
            dto = []
            for c in contributions:
                dto.append(ContributionDTO(c.id, c.title, c.type, c.points, c.author.username, c.url, c.text, c.date))

            serializer = ContributionDTOSerializer(dto, many=True)
            return Response(serializer.data)

        #obtenir les submissions tipus ask
        elif id is None and filter is None and type is not None:

            if filter == 'ask':
                contributions = Contribution.objects.filter(type="ask").order_by('-points')

                dto = []
                for c in contributions:
                    dto.append(ContributionDTO(c.id, c.title, c.type, c.points, c.author.username, c.url, c.text, c.date))

                serializer = ContributionDTOSerializer(dto, many=True)
                return Response(serializer.data)

            else:
                return Response({
                    "type": ["This field value must be ask."]
                }, status=status.HTTP_400_BAD_REQUEST)

        #obtenir totes les submissions ordenades per punts o data
        elif id is None and filter is not None and type is None:

            if filter == 'points':
                contributions = Contribution.objects.order_by('-points')

                dto = []
                for c in contributions:
                    dto.append(ContributionDTO(c.id, c.title, c.type, c.points, c.author.username, c.url, c.text, c.date))

                serializer = ContributionDTOSerializer(dto, many=True)
                return Response(serializer.data)

            elif filter == 'news':
                contributions = Contribution.objects.all().order_by('-date')

                dto = []
                for c in contributions:
                    dto.append(ContributionDTO(c.id, c.title, c.type, c.points, c.author.username, c.url, c.text, c.date))

                serializer = ContributionDTOSerializer(dto, many=True)
                return Response(serializer.data)
            else:
                return Response({
                    "filter": ["This field value must be ask."]
                }, status=status.HTTP_400_BAD_REQUEST)

        #obtenir totes les submissions
        elif id is None and filter is None and type is None:
            contributions = Contribution.objects.all().order_by('-points')
            dto = []
            for c in contributions:
                dto.append(ContributionDTO(c.id, c.title, c.type, c.points, c.author.username, c.url, c.text, c.date))

            serializer = ContributionDTOSerializer(dto, many=True)
            return Response(serializer.data)

        else:
            return Response({
                "query": ["You must only provide one optional query parameter."]
            }, status=status.HTTP_400_BAD_REQUEST)

    else:
        data = JSONParser().parse(request)
        serializer = ContributionCreationDTOSerializer(data=data)
        if serializer.is_valid():
            c = Contribution()
            c.title = serializer.data.get('title')
            c.url = serializer.data.get('url')
            c.author = auth.user
            if not c.url:
                c.text = serializer.data.get('text')
                c.type = 'ask'
            else:
                match = Contribution.objects.filter(url=c.url).exists()
                if match:
                    return Response({
                        "query": ["Is already defined in this url: /api/submissions/",
                                  str(Contribution.objects.get(url=c.url).id)]
                    }, status=status.HTTP_302_FOUND)

            c.save()
            if serializer.data.get('url') and serializer.data.get('text'):
                com = Comment()
                com.author = auth.user
                com.text = serializer.data.get('text')
                com.contribution = Contribution.objects.get(url=c.url)
                com.save()
            ud = UserDetail.objects.get(user=auth.user)
            ud.karma = ud.karma + 1
            ud.save()

            serializer = ContributionDTOSerializer(c)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','POST'])
def submission_fav_api(request):
    token = request.META.get('HTTP_AUTHORIZATION')
    #aixo cal??
    if token is None:
        return Response({
            "authentication": ["This field is required."]
        }, status=status.HTTP_401_UNAUTHORIZED)

    try:
        auth = Token.objects.get(key=token)
    except Token.DoesNotExist:
        return Response({
            "authentication": ["This key is invalid."]
        }, status=status.HTTP_401_UNAUTHORIZED)

    id = request.GET.get("id", None)

    if id is None:
        return Response({
            "id": ["This field is required."]
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(username=id)
    except User.DoesNotExist:
        return Response({
            "id": ["User does not exist."]
        }, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        #creiem que no sha de posar, es pk surti el tick per votar
        #votes = ContributionVote.objects.filter(user=request.user)
        votedcontributions = ContributionVote.objects.filter(user=User.objects.get(username=request.GET.get('id')))
        dto = []
        for c in votedcontributions:
            dto.append(ContributionDTO(c.contribution.id, c.contribution.title, c.contribution.type, c.contribution.points, c.contribution.author.username, c.contribution.url, c.contribution.text, c.contribution.date))

        serializer = ContributionDTOSerializer(dto, many=True)
        return Response(serializer.data)

    #elif request.method == 'POST':

@api_view(['GET', 'POST'])
def comments_api(request) :
    token = request.META.get('HTTP_AUTHORIZATION')
    if token is None:
        return Response({
            "authentication": ["This field is required."]
        }, status=status.HTTP_401_UNAUTHORIZED)

    try:
        auth = Token.objects.get(key=token)
    except Token.DoesNotExist:
        return Response({
            "authentication": ["This key is invalid."]
        }, status=status.HTTP_401_UNAUTHORIZED)

    id = request.GET.get("id", None)

    if id is None:
        return Response({
            "id": ["This field is required."]
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(username=id)
    except User.DoesNotExist:
        return Response({
            "id": ["User does not exists."]
        }, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        author = User.objects.get(username=id)
        comments = Comment.objects.filter(author=author).order_by('level', '-date')
        dto = []

        for c in comments:
            if c.father is None:
                f = None
            else:
                f = c.father.id
            dto.append(CommentDTO(c.id, c.level, c.author, c.text, c.votes, c.date, c.contribution.id, f))

        serializer = CommentDTOSerializer(dto, many=True)

        return Response(serializer.data)




@api_view(['GET', 'PUT'])
def profile_api(request):
    token = request.META.get('HTTP_AUTHORIZATION')

    if token is None:
        return Response({
            "authentication": ["This field is required."]
        }, status=status.HTTP_401_UNAUTHORIZED)

    try:
        auth = Token.objects.get(key=token)
    except Token.DoesNotExist:
        return Response({
            "authentication": ["This key is invalid."]
        }, status=status.HTTP_401_UNAUTHORIZED)

    id = request.GET.get("id", None)

    if id is None:
        return Response({
            "id": ["This field is required."]
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        username = request.GET.get('id')
        user = User.objects.get(username=username)
        userDetail = UserDetail.objects.get(user=user)
        userDTO = UserDTO(user.username, user.email, userDetail.karma, userDetail.about, userDetail.created)

        if request.method == 'PUT':
            if auth.user != user:
                return Response({
                    "Unauthorized": ["You're not allowed to modify this profile."]
                }, status=status.HTTP_401_UNAUTHORIZED)

            data = JSONParser().parse(request)
            serializer = UserDTOSerializer(userDTO, data=data)
            if serializer.is_valid():
                serializer.save()
                userDetail.about = serializer.data.get('about')
                userDetail.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


        elif request.method == 'GET':
            serializer = UserDTOSerializer(userDTO)
            return Response(serializer.data)

    except User.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


@api_view(['POST', 'DELETE'])
def vote_contribution_api(request, id):
    token = request.META.get('HTTP_AUTHORIZATION')

    if token is None:
        return Response({
            "authentication": ["This field is required."]
        }, status=status.HTTP_401_UNAUTHORIZED)

    try:
        auth = Token.objects.get(key=token)
    except Token.DoesNotExist:
        return Response({
            "authentication": ["This key is invalid."]
        }, status=status.HTTP_401_UNAUTHORIZED)

    try:
        c = Contribution.objects.get(id=id)
        voted = ContributionVote.objects.filter(user=auth.user, contribution=c)
        if request.method == 'POST':
            if voted:
                return Response({
                    "id": ["Contribution identified by id has already been voted by this user"]
                }, status=status.HTTP_302_FOUND)
            else:
                c.points = c.points + 1
                c.save()
                contributionvote = ContributionVote()
                contributionvote.user = auth.user
                contributionvote.contribution = c
                contributionvote.save()
                serializer = ContributionDTOSerializer(c)
                return Response(serializer.data,status=status.HTTP_200_OK)
        else:
            if not voted:
                return Response({
                    "id": ["Contribution identified by id has not been voted by this user"]
                }, status=status.HTTP_302_FOUND)
            else:
                c.points = c.points - 1
                c.save()
                voted.delete()
                serializer = ContributionDTOSerializer(c)
                return Response(serializer.data, status=status.HTTP_200_OK)

    except Contribution.DoesNotExist:
        return Response({
            "id": ["This id is not found."]
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST', 'DELETE'])
def vote_comment_api(request, id):
    token = request.META.get('HTTP_AUTHORIZATION')

    if token is None:
        return Response({
            "authentication": ["This field is required."]
        }, status=status.HTTP_401_UNAUTHORIZED)

    try:
        auth = Token.objects.get(key=token)
    except Token.DoesNotExist:
        return Response({
            "authentication": ["This key is invalid."]
        }, status=status.HTTP_401_UNAUTHORIZED)

    try:
        c = Comment.objects.get(id=id)
        voted = CommentVote.objects.filter(user=auth.user, comment=c)
        if request.method == 'POST':
            if voted:
                return Response({
                    "id": ["Comment identified by id has already been voted by this user"]
                }, status=status.HTTP_302_FOUND)
            else:
                c.votes = c.votes + 1
                c.save()
                commentvote = CommentVote()
                commentvote.user = auth.user
                commentvote.comment = c
                commentvote.save()
                serializer = CommentDTOSerializer(c)
                return Response(serializer.data,status=status.HTTP_200_OK)
        else:
            if not voted:
                return Response({
                    "id": ["Comment identified by id has not been voted by this user"]
                }, status=status.HTTP_302_FOUND)
            else:
                c.votes = c.votes - 1
                c.save()
                voted.delete()
                serializer = CommentDTOSerializer(c)
                return Response(serializer.data, status=status.HTTP_200_OK)

    except Comment.DoesNotExist:
        return Response({
            "id": ["This id is not found."]
        }, status=status.HTTP_404_NOT_FOUND)