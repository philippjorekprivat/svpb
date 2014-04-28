# -*- coding: utf-8 -*-

# Create your views here.

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views.generic import View, ListView, CreateView, FormView
from django.contrib.auth.models import User 
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Sum
from django.contrib.auth import logout
from django.forms.models import modelformset_factory
from django.utils.safestring import mark_safe
from django.utils.html import escape

import django_tables2

import models, forms
# import networkx as nx 

import unicodedata

#################

def isVorstand (user):
    return user.groups.filter(name='Vorstand')

class isVorstandMixin (object):
    @method_decorator(user_passes_test(isVorstand, login_url="/keinVorstand/"))
    def dispatch(self, *args, **kwargs):
        return super(isVorstandMixin, self).dispatch(*args, **kwargs)
    
###############

def logout_view (request):
    # print "logout view" 
    logout(request)
    return  render (request, "registration/logged_out.html", {})
###############

def TableFactory (name, attrs, l, meta={}):
    """takes
    - a name for the new django_tables2 class
    - a dictoranry with column_name: column_types
    - a list of data to be used for the table 

    return klass 
    """

    metadict = dict(attrs={"class":"paleblue",
                            "orderable":"True",
                           # "width":"90%"
                    })


    metadict.update(meta)
    attrs['Meta'] = type('Meta',
                         (),
                         metadict,
                        )
    
    klass = type (name, (django_tables2.Table,), attrs)

    t = klass(l)
    return t 

def NameTableFactory (name, attrs, l):
    """
    A Factory for django_tables2 with dynamic colums.
    Always adds a Nachame, Vorname column to the given attributes 
    """

    nameattrs = {'last_name': django_tables2.Column(verbose_name="Nachname"),
                'first_name': django_tables2.Column(verbose_name="Vorname"),
                }
    nameattrs.update(attrs)

    return TableFactory (name, nameattrs, l,
                         meta={'sequence': ('last_name', 'first_name', '...')})

###############


class UpdateMeldungView (View):

    def get(self,request, *args, **kwargs):
        myForm = forms.MeldungForm()

        # which questions should get an initial check?
        aufgabenMitMeldung = [m.aufgabe.id for m in 
                                models.Meldung.objects.filter(melder_id=request.user.id)]
        # print aufgabenMitMeldung
        
        return render (request,
                       "arbeitsplan_meldung.html",
                       dictionary = {'form': myForm,
                                     'groups': [ (g.id,
                                                  g.gruppe,
                                                  [(a.id,
                                                    a.aufgabe,
                                                    a.datum if a.datum else "",
                                                    a.id in aufgabenMitMeldung, 
                                                    )
                                                    for a in models.Aufgabe.objects.filter(gruppe__exact=g)],
                                                  )
                                                 for g in models.Aufgabengruppe.objects.all()]},
                       )

    def post (self,request, *args, **kwargs):

        myForm = forms.MeldungForm (request.POST)
        if myForm.is_valid():
            # print "processing valid form"
            # print myForm.cleaned_data

            for k, userInput in myForm.cleaned_data.iteritems():
                aid = int(k.split('a')[1])
                # print aid, userInput

                # try to find a meldung with that aid and for this user
                try: 
                    meldungStatus = models.Meldung.objects.get (aufgabe_id=aid,
                                                                melder_id=request.user.id)
                except:
                    # print "get failed"
                    meldungStatus = False

                # print "mledung status",  meldungStatus
                    
                if userInput:
                    # we have to add or update the corresponding meldung
                    if meldungStatus:
                        # update existing object 
                        newMeld = models.Meldung (aufgabe = models.Aufgabe.objects.get(id=aid),
                                                  erstellt = meldungStatus.erstellt, 
                                                  melder = request.user, 
                                                  id = meldungStatus.id)
                    else:
                        #create a new one:
                        newMeld = models.Meldung (aufgabe = models.Aufgabe.objects.get(id=aid),
                                                  melder = request.user, 
                                                  )
                        
                    # print newMeld
                    newMeld.save()
                else:
                    # user does not work on a particular job;
                    # if meldung exists, delete it

                    if meldungStatus:
                        meldungStatus.delete()
                        
                    
            
            return redirect ('arbeitsplan-meldung')

        # print "processing INvalid form"
        return HttpResponse ("Form was invalid - what to do?")


class AufgabenTable (django_tables2.Table):
    verantwortlicher = django_tables2.Column (accessor="verantwortlich.last_name",
                                              verbose_name="Verantwortlicher")
    class Meta:
        model = models.Aufgabe
        attrs = {"class": "paleblue"}
        # fields=("aufgabe", "datum", django_tables2.A("verantwortlich.last_name"), "gruppe", "anzahl", "bemerkung")
        fields=("aufgabe", "datum", "gruppe", "anzahl", "bemerkung")

        # TODO: anzahl muss man wahrscheinlich auf die ANzahl FREIE Plaetze umrechnen!?!?
        
class ListAufgabenView (ListView):

    # model = models.Aufgabe
    template_name = "arbeitsplan_aufgabenlist.html"

    def get_queryset (self):
        table = AufgabenTable(models.Aufgabe.objects.all())
        django_tables2.RequestConfig(self.request).configure(table)
        return table

class ZuteilungTable (django_tables2.Table):
    ausfuehrer_last = django_tables2.Column (accessor="ausfuehrer.last_name",
                                              verbose_name="Ausführer")
    class Meta:
        model = models.Zuteilung
        attrs = {"class": "paleblue"}

        fields = ("aufgabe", )
        
class ListZuteilungenView (ListView):

    ## def get_context_data (self, object_list):
    ##     print object_list
    ##     return object_list 
        
    def get_queryset (self):
        if "all" in  self.request.path: 
            table = ZuteilungTable(models.Zuteilung.objects.all())
        else:
            table = ZuteilungTable(models.Zuteilung.objects.filter (ausfuehrer =self.request.user))
        # 
        django_tables2.RequestConfig(self.request).configure(table)
        return table 
        
    template_name = "arbeitsplan_zuteilunglist.html" 


class MeldungTable (django_tables2.Table):
    melder_last = django_tables2.Column (accessor="melder.last_name",
                                         verbose_name="Nachname")
    melder_first = django_tables2.Column (accessor="melder.first_name",
                                         verbose_name="Vorname")
    aufgabe =  django_tables2.Column (accessor="aufgabe",
                                         verbose_name="Aufgabe")
    class Meta:
        model = models.Meldung
        attrs = {"class": "paleblue"}

        exclude = ("erstellt","veraendert", 'melder')
        
        
class ListMeldungenView (isVorstandMixin, ListView):
    # model = models.Meldung
    template_name = "arbeitsplan_meldunglist.html"
    
    def get_queryset (self):
        table = MeldungTable(models.Meldung.objects.all())
        django_tables2.RequestConfig(self.request).configure(table)
        return table



class CreateLeistungView (CreateView):
    model = models.Leistung
    form_class = forms.CreateLeistungForm 
    template_name = "arbeitsplan_createLeistung.html"

    def form_valid (self, form):
        leistung = form.save (commit=False)
        leistung.melder = self.request.user
        leistung.save()
        return HttpResponseRedirect(self.success_url)

####################################


class ListLeistungView (ListView):
    template_name = "arbeitsplan_listLeistung.html"
    def get_queryset(self):
        res = []
        for s in models.Leistung.STATUS:
            qs = models.Leistung.objects.filter(status=s[0],
                                                melder=self.request.user,
                                                )
            sum = qs.aggregate(Sum('zeit'))
            res.append((s[0], s[1], qs, sum['zeit__sum']))
            
        return res
    
        # return models.Leistung.objects.filter(melder=self.request.user)
    


class LeistungBearbeitenView (isVorstandMixin, View):
    def get(self, request, zustaendig, *args, **kwargs):
        # print zustaendig
        if zustaendig=="me": 
            mainqs = models.Leistung.objects.filter(aufgabe__verantwortlich=request.user)
        else:
            mainqs = models.Leistung.objects.all()

        # and filter further only the open or rueckfragen;
        # for simplicity, we exlude the other ones:
        
        mainqs = mainqs.exclude(status=models.Leistung.ACK
                                ).exclude(status=models.Leistung.NEG)
        print "view qs: "
        print [l.id for l in mainqs]
        return render (request,
                       "arbeitsplan_leistungbearbeiten.html",
                       dictionary = {
                           # 'formset': formset,
                           'qs': mainqs,
                           'statusvalues': models.Leistung.STATUS, 
                           },
                       )
            
    def post (self, request, zustaendig, *args, **kwargs):
        # clean up data by hand here
        print request.POST 
        data = {}
        for k, v in request.POST.iteritems():
            try: 
                tag, num = k.split('-')
                if (tag == 'id_status' or tag=='id_bemerkungVorstand'):
                    if not num in data.keys():
                        data[num] = {'id_status': "",
                                     'id_bemerkungVorstand': "",
                        }
                    data[num][tag] = v
            except:
                pass 

        print data

        # and now save the updated values in the data
        for k,v in data.iteritems():
            # they should all exist!
            ## print "----------"
            ## print k, v
            ## print type(v['id_bemerkungVorstand'])
            l = models.Leistung.objects.get (id = int(k))
            l.bemerkungVorstand = v['id_bemerkungVorstand']
            l.status = v['id_status']
                                 ## status = v['id_status'],
                                 ## 
                                 
            l.save()
            print l

        # TODO: bei Rueckfrage koennte man eine email senden? oder immer?
        
        return redirect ('/arbeitsplan/leistungenBearbeiten/z=all')    
##########################    


def SaldenTableFactory (l):

    attrs = {}
    for s in models.Leistung.STATUS:
        attrs[s[0]] = django_tables2.Column(verbose_name=s[1])

    t = NameTableFactory ("salden", attrs, l)
    return t 


class NameFilterView (View):
    
    def applyFilter (self, request):

        qs = models.User.objects.all()

        form = self.filterFormClass(request.GET)
        if form.is_valid():
            if 'filter' in request.GET:
                last_name = form.cleaned_data['last_name']

                if last_name <> "":
                    qs= qs.filter (last_name__icontains=last_name)
                
                first_name = form.cleaned_data['first_name']
                if first_name <> "":
                    qs= qs.filter (first_name__icontains=first_name)
                
        else:
            print "filter not valid"
            
        return (qs, form)
        
class Salden(isVorstandMixin, NameFilterView):

    filterFormClass = forms.NameFilterForm
    
    def get (self, request, *args, **kwargs):

        userQs, filterForm = self.applyFilter(request)

        res = []
        for u in userQs.order_by('last_name', 'first_name'):
            tmp = {}
            tmp['last_name'] = u.last_name
            tmp['first_name'] = u.first_name
            tmp['box'] = ("box-" + str(u.id), True) 
            qs = models.Leistung.objects.filter(melder=u)
            for s in  models.Leistung.STATUS:
                zeit = qs.filter(status=s[0]
                                ).aggregate(Sum('zeit'))['zeit__sum']
                tmp[s[0]] = zeit

            res.append(tmp)
            
        table = SaldenTableFactory(res)

        django_tables2.RequestConfig (request, paginate={"per_page": 25}).configure(table)

        # for filtering:

        return render (request,
                       "arbeitsplan_salden.html",
                        {'salden': table,
                         'filter': filterForm, 
                        })
    
    def post (self, request, *args, **kwargs):
        print request
        return redirect ("arbeitsplan-salden")
    
    
##########################    

class ValuedCheckBoxColumn (django_tables2.columns.Column):
    """A checkbox column where a pair of values is expected:
    name and whether the box is checked or not.
    Control tags:
    -1: show no field
    0: unchecked checkbox
    1: checked checkbox 
    """
    
    def render (self, value):
        if value[0] == -1:
            return ""
        
        return mark_safe ('<input type="checkbox" value="1" name="' +
                          escape(value[1]) +
                          '" ' +
                          ("checked" if value[0]==1 else "") +
                          '/>'
                          )
    
    
    

def ZuteilungsTableFactory (l, aufgabenQs):
    attrs={}
    for a in aufgabenQs:
        tag = unicodedata.normalize('NFKD', a.aufgabe).encode('ASCII', 'ignore')
        attrs[tag] = ValuedCheckBoxColumn(verbose_name=a.aufgabe,
                                          orderable=False)

    t = NameTableFactory ('ZuteilungsTable', attrs, l)
 
    return t 
        
class ManuelleZuteilungView (isVorstandMixin, NameFilterView):
    """Manuelles Eintragen von Zuteilungen
    """

    filterFormClass = forms.AufgabengruppeFilterForm
    
    def get (self,request, *args, **kwargs):
        """Baue eine Tabelle zusammen, die den Zuteilungen aus der DAtenbank
        entspricht."""

        userQs, filterForm = self.applyFilter (request)

        if filterForm.cleaned_data['aufgabengruppe'] <> None:
            print filterForm.cleaned_data['aufgabengruppe']
            aufgabenQs = models.Aufgabe.objects.filter (gruppe__gruppe = filterForm.cleaned_data['aufgabengruppe'])
        else:
            aufgabenQs = models.Aufgabe.objects.all()
            
        ztlist = []
        statuslist = {}
        aufgaben = dict([(unicodedata.normalize('NFKD', a.aufgabe).encode('ASCII', 'ignore'),
                          (-1, 'x'))
                          for a in aufgabenQs])

        for u in userQs: 
            tmp = {'last_name': u.last_name,
                    'first_name': u.first_name,
                    }
            # print 'user:', u.id 
            tmp.update(aufgaben)
            mQs =  models.Meldung.objects.filter(melder=u)
            if filterForm.cleaned_data['aufgabengruppe'] <> None:
                mQs = mQs.filter(aufgabe__gruppe__gruppe =  filterForm.cleaned_data['aufgabengruppe'])
            for m in mQs: 
                tag = unicodedata.normalize('NFKD', m.aufgabe.aufgabe).encode('ASCII', 'ignore')
                tmp[tag] = (0, 'box_'+  str(u.id)+"_"+str(m.aufgabe.id))
                statuslist[str(u.id)+"_"+str(m.aufgabe.id)]='0'

            zQs =  models.Zuteilung.objects.filter(ausfuehrer=u)
            if filterForm.cleaned_data['aufgabengruppe'] <> None:
                zQs = zQs.filter(aufgabe__gruppe__gruppe =  filterForm.cleaned_data['aufgabengruppe'])
            
            for z in zQs: 
                tag = unicodedata.normalize('NFKD', z.aufgabe.aufgabe).encode('ASCII', 'ignore')
                tmp[tag] = (1, 'box_'+ str(u.id)+"_"+str(z.aufgabe.id))
                statuslist[str(u.id)+"_"+str(z.aufgabe.id)]='1'


                
            ztlist.append(tmp)

        ## print ztlist
        ## print statuslist
        zt = ZuteilungsTableFactory(ztlist, aufgabenQs)
        django_tables2.RequestConfig (request, paginate={"per_page": 25}).configure(zt)

        return render (request,
                       'arbeitsplan_manuelleZuteilung.html',
                       {'table': zt,
                        'status': ';'.join([k+'='+v for k, v in statuslist.iteritems()]),
                        'filter': filterForm, 
                        })
    
    def post (self,request, *args, **kwargs):
        # print request.body 
        ## print (request.POST )
        ## print (request.POST.get('status') )
        ## print (request.POST.getlist('box') )

        ## filterForm = self.filterFormClass (request.POST)
        
        previousStatus = dict([ tuple(s.split('=') )
                   for s in 
                    request.POST.get('status').split(';')
                  ])

        print "prevState:"
        print previousStatus

        ## for item in request.POST.iteritems():
        ##     # containts tuple: name, value
        ##     # print item
        ##     if item[0][:4] == "box_":
        ##         print "item: ", item

        newState = dict([ (item[0][4:], item[1])
                     for item in request.POST.iteritems()
                     if item[0][:4] == "box_"
                    ])

        print "newState"
        print newState

        # find all items in  newState  that have a zero in prevState
        # add that zuteilung
        for k,v in newState.iteritems():
            if previousStatus[k] == '0':
                print "add ", k
                user, aufgabe = k.split('_')
                z = models.Zuteilung(aufgabe = models.Aufgabe.objects.get(id=int(aufgabe)),
                                     ausfuehrer = models.User.objects.get(id=int(user)),
                                     )
                z.save()


        # find all items in prevState with a 1 there that do no appear in newState
        # remove that zuteilung
        for k,v in previousStatus.iteritems():
            if v=='1' and k not in newState:
                print "delete ", k
                user, aufgabe = k.split('_')
                z = models.Zuteilung.objects.get (aufgabe = models.Aufgabe.objects.get(id=int(aufgabe)),
                                                  ausfuehrer = models.User.objects.get(id=int(user)),
                                                 )
                z.delete()

        # TODO: emails senden? 
        return redirect ("arbeitsplan-manuellezuteilung")

    
##########################    
    
class ErstelleZuteilungView (View):
    """Automatisches Berechnen von Zuteilungen"""
    
    def get (self,request, *args, **kwargs):
        # Vorgehen:
        # - alle automatisch erstellten Zuordnungen loecshen
        # - aus den Meldungen einen bipartiten Graph erstellen (networkx nutzen)
        # - aus dem Graphen die manuell erstellten Zuordnungen entfernen
        # - maximales Matching ausrechnen
        # - als Zuordnungen in Tabelle eintragen
        # - redirect zur Zuordnungsanzeigen machen

        ## qs = models.Zuteilung.objects.filter (automatisch__exact=True)
        ## for o in qs:
        ##     o.delete()

        ## #######
        ## # den Graph bauen
        ## G = nx.Graph()
        ## # alle Mitglieder einfuegen
        ## for m in models.User.objects.all():
        ##     G.add_node ('P' + str(m.id))

        ## for a in models.Aufgabe.objects.all():
        ##     for i in range(a.anzahl):
        ##         G.add_node ('A' + str(a.id) + ':' + str(i))

        ## for m in models.Meldung.objects.all():
        ##     G.add_edge ('')
        
            
        return redirect ('arbeitsplan-zuteilunglist')

#####################


    
        
                          
